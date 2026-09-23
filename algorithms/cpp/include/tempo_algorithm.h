// algorithms/cpp/include/tempo_algorithm.h
//
// Base interface for a real-time tempo (BPM) detection algorithm.
// Every algorithm derives from this class. This makes it possible to:
//   - call all of them from Python in the same way (via one pybind11 template)
//   - add new algorithms easily
//   - reuse the very same sources in a Daisy Seed project without rewriting
//
#pragma once

#include <cstddef>

namespace tempo {

class TempoAlgorithm {
public:
    virtual ~TempoAlgorithm() = default;

    /// Reset the algorithm state for the given sample rate.
    /// Called once before streaming starts.
    virtual void reset(float sample_rate) = 0;

    /// Process a block of mono samples in the [-1, 1] range.
    /// On Daisy Seed this receives exactly one audio callback block (typically 48..1024 samples).
    virtual void process_block(const float* samples, std::size_t num_samples) = 0;

    /// Current tempo estimate in BPM (0 if not estimated yet).
    /// May be called arbitrarily often, so it must be cheap.
    virtual float get_bpm() const = 0;

    /// Algorithm name for reports/UI.
    virtual const char* name() const = 0;
};

} // namespace tempo
