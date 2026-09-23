// algorithms/cpp/include/energy_bpm.h
//
// EnergyBPM - real-time BPM detector based on energy peaks.
//
// Follows the classic approach (see Scheirer 1998, Patin):
//   1. The sample stream is split into short ~23 ms windows
//   2. The mean energy (sum of squares / N) is computed for each window
//   3. A sliding history of ~1 second (43 windows) is kept
//   4. Adaptive threshold = mean(history) + k * stddev(history)
//   5. If the current energy > threshold and >= min_gap has passed since the last beat, it is a beat
//   6. BPM = median of the recent estimates (from the intervals between beats)
//
// Pros:        O(1) per sample, tiny memory footprint (< 400 bytes of state),
//              no FFT required - a great fit for Cortex-M7.
// Limitations: works best on percussive music, weak on legato/strings.
//
#pragma once

#include "tempo_algorithm.h"
#include <array>
#include <cstddef>
#include <cstdint>

namespace tempo {

class EnergyBPM : public TempoAlgorithm {
public:
    explicit EnergyBPM(float min_bpm     = 60.0f,
                       float max_bpm     = 200.0f,
                       float threshold_k = 1.4f);

    void reset(float sample_rate) override;
    void process_block(const float* samples, std::size_t num_samples) override;
    float get_bpm() const override { return current_bpm_; }
    const char* name() const override { return "EnergyBPM (C++)"; }

private:
    void close_window();
    void register_beat(std::int64_t at_sample);

    // Parameters
    float min_bpm_;
    float max_bpm_;
    float threshold_k_;

    // Current energy integration window
    float sample_rate_{0.0f};
    std::size_t window_size_{0};
    std::size_t window_pos_{0};
    float window_energy_acc_{0.0f};

    // Ring buffer of the energy history (~1 second)
    static constexpr std::size_t HISTORY_SIZE = 43;
    std::array<float, HISTORY_SIZE> energy_history_{};
    std::size_t history_idx_{0};
    std::size_t history_count_{0};

    // Inter-beat interval tracking
    std::int64_t samples_processed_{0};
    std::int64_t last_beat_sample_{-1};
    std::int64_t min_beat_gap_samples_{0};

    // Sliding window of BPM estimates for median filtering
    static constexpr std::size_t MAX_INTERVALS = 24;
    std::array<float, MAX_INTERVALS> recent_bpms_{};
    std::size_t bpms_idx_{0};
    std::size_t bpms_count_{0};

    float current_bpm_{0.0f};
};

} // namespace tempo
