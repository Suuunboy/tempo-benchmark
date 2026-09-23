// algorithms/cpp/src/autocorr_bpm.cpp
#include "autocorr_bpm.h"

#include <algorithm>
#include <cmath>

namespace tempo {

AutocorrBPM::AutocorrBPM(float min_bpm, float max_bpm)
    : min_bpm_(min_bpm), max_bpm_(max_bpm) {}

void AutocorrBPM::reset(float sample_rate) {
    sample_rate_ = sample_rate;

    // ~10 ms window -> the envelope runs at ~100 Hz
    window_size_ = static_cast<std::size_t>(sample_rate_ * 0.010f);
    if (window_size_ < 32) window_size_ = 32;
    envelope_rate_ = sample_rate_ / static_cast<float>(window_size_);

    // 6 seconds of envelope is enough to catch any tempo from 60 BPM up
    envelope_size_ = static_cast<std::size_t>(envelope_rate_ * 6.0f);
    envelope_.assign(envelope_size_, 0.0f);
    envelope_idx_   = 0;
    envelope_count_ = 0;

    window_pos_         = 0;
    window_energy_acc_  = 0.0f;

    // Recompute BPM every ~0.5 s
    compute_period_windows_ = static_cast<std::size_t>(envelope_rate_ * 0.5f);
    windows_since_compute_  = 0;

    for (std::size_t i = 0; i < SMOOTH_SIZE; ++i) bpm_history_[i] = 0.0f;
    bpm_history_idx_   = 0;
    bpm_history_count_ = 0;

    current_bpm_ = 0.0f;
}

void AutocorrBPM::close_window() {
    // RMS energy of the window
    float energy = window_energy_acc_ / static_cast<float>(window_size_);
    energy = std::sqrt(energy);

    envelope_[envelope_idx_] = energy;
    envelope_idx_ = (envelope_idx_ + 1) % envelope_size_;
    if (envelope_count_ < envelope_size_) ++envelope_count_;

    window_energy_acc_ = 0.0f;
    window_pos_        = 0;

    ++windows_since_compute_;
    if (windows_since_compute_ >= compute_period_windows_ &&
        envelope_count_ >= envelope_size_ / 2) {
        compute_bpm();
        windows_since_compute_ = 0;
    }
}

void AutocorrBPM::compute_bpm() {
    // Unroll the ring buffer into chronological order
    std::vector<float> env(envelope_count_);
    for (std::size_t i = 0; i < envelope_count_; ++i) {
        std::size_t pos;
        if (envelope_count_ < envelope_size_) {
            // Buffer not full yet: data lies in [0, envelope_count_)
            pos = i;
        } else {
            // The oldest element is at envelope_idx_, wrap around
            pos = (envelope_idx_ + i) % envelope_size_;
        }
        env[i] = envelope_[pos];
    }

    // Subtract the mean (required for a proper ACF)
    float mean = 0.0f;
    for (float v : env) mean += v;
    mean /= static_cast<float>(env.size());
    for (float& v : env) v -= mean;

    // Novelty function: half-wave rectified first difference (HWR of d/dt) -
    // emphasizes attacks and suppresses decays
    std::vector<float> novelty(env.size(), 0.0f);
    for (std::size_t i = 1; i < env.size(); ++i) {
        const float d = env[i] - env[i - 1];
        novelty[i] = (d > 0.0f) ? d : 0.0f;
    }

    // Autocorrelation lag range, in envelope samples
    std::size_t lag_min = static_cast<std::size_t>(envelope_rate_ * 60.0f / max_bpm_);
    std::size_t lag_max = static_cast<std::size_t>(envelope_rate_ * 60.0f / min_bpm_);
    if (lag_max >= novelty.size()) lag_max = novelty.size() - 1;
    if (lag_min < 1) lag_min = 1;
    if (lag_min >= lag_max) return;

    // Direct ACF, O(N*L). On ARM that is ~50k operations every 0.5 s, cheap.
    float best_acf = -1e30f;
    std::size_t best_lag = lag_min;
    for (std::size_t lag = lag_min; lag <= lag_max; ++lag) {
        float acc = 0.0f;
        const std::size_t n = novelty.size() - lag;
        for (std::size_t i = 0; i < n; ++i) {
            acc += novelty[i] * novelty[i + lag];
        }
        if (acc > best_acf) {
            best_acf = acc;
            best_lag = lag;
        }
    }

    const float bpm = 60.0f * envelope_rate_ / static_cast<float>(best_lag);

    // Median smoothing over the last 8 estimates
    bpm_history_[bpm_history_idx_] = bpm;
    bpm_history_idx_ = (bpm_history_idx_ + 1) % SMOOTH_SIZE;
    if (bpm_history_count_ < SMOOTH_SIZE) ++bpm_history_count_;

    float sorted[SMOOTH_SIZE];
    for (std::size_t i = 0; i < bpm_history_count_; ++i) sorted[i] = bpm_history_[i];
    std::sort(sorted, sorted + bpm_history_count_);
    current_bpm_ = sorted[bpm_history_count_ / 2];
}

void AutocorrBPM::process_block(const float* samples, std::size_t num_samples) {
    for (std::size_t i = 0; i < num_samples; ++i) {
        const float s = samples[i];
        window_energy_acc_ += s * s;
        ++window_pos_;
        if (window_pos_ >= window_size_) {
            close_window();
        }
    }
}

} // namespace tempo
