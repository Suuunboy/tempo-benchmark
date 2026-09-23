// algorithms/cpp/include/autocorr_bpm.h
//
// AutocorrBPM - real-time BPM detector based on autocorrelation of the energy envelope.
//
// Idea:
//   1. Audio is converted into an energy envelope (RMS over short ~10 ms windows)
//      -> ~440x rate reduction (from 44.1 kHz down to ~100 Hz)
//   2. The envelope is kept in a ~6 second ring buffer
//   3. Every ~0.5 s an autocorrelation is computed over the lag range
//      corresponding to 60..200 BPM
//   4. The lag with the maximum ACF is taken -> BPM = 60 * envelope_rate / lag
//   5. The final estimate is the median of the last 8 values (stabilization)
//
// Pros:  more robust on non-percussive music, captures periodicity better,
//        does not depend on individual beats
// Cost:  O(N * L) autocorrelation every 0.5 s, where N ~ 600, L ~ 70.
//        On a Cortex-M7 that is about 40-50k operations every 0.5 s - acceptable.
//
#pragma once

#include "tempo_algorithm.h"
#include <cstddef>
#include <cstdint>
#include <vector>

namespace tempo {

class AutocorrBPM : public TempoAlgorithm {
public:
    explicit AutocorrBPM(float min_bpm = 60.0f, float max_bpm = 200.0f);

    void reset(float sample_rate) override;
    void process_block(const float* samples, std::size_t num_samples) override;
    float get_bpm() const override { return current_bpm_; }
    const char* name() const override { return "AutocorrBPM (C++)"; }

private:
    void close_window();
    void compute_bpm();

    // Parameters
    float min_bpm_;
    float max_bpm_;

    // Energy (RMS) integration window
    float sample_rate_{0.0f};
    std::size_t window_size_{0};
    std::size_t window_pos_{0};
    float window_energy_acc_{0.0f};
    float envelope_rate_{0.0f}; // envelope sample rate, Hz

    // Envelope ring buffer
    std::vector<float> envelope_;
    std::size_t envelope_size_{0};
    std::size_t envelope_idx_{0};
    std::size_t envelope_count_{0};

    // When to recompute BPM
    std::size_t windows_since_compute_{0};
    std::size_t compute_period_windows_{0};

    // Median smoothing of BPM
    static constexpr std::size_t SMOOTH_SIZE = 8;
    float bpm_history_[SMOOTH_SIZE]{};
    std::size_t bpm_history_idx_{0};
    std::size_t bpm_history_count_{0};

    float current_bpm_{0.0f};
};

} // namespace tempo
