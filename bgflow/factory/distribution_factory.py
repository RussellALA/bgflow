import torch
import bgflow as bg


__all__ = ["make_distribution"]

# === Prior Factory ===


def make_distribution(distribution_type, shape, **kwargs):
    if distribution_type in DISTRIBUTION_FACTORIES:
        factory = DISTRIBUTION_FACTORIES[distribution_type]
    else:  # distribution_type is the factory itself
        factory = distribution_type

    return factory(shape=shape, **kwargs)


def _make_uniform_distribution(shape, device=None, dtype=None, **kwargs):
    defaults = {"low": torch.zeros(shape), "high": torch.ones(shape)}
    defaults.update(kwargs)
    for key in defaults:
        if isinstance(defaults[key], torch.Tensor):
            defaults[key] = defaults[key].to(device=device, dtype=dtype)
    return bg.UniformDistribution(**defaults)


def _make_normal_distribution(shape, device=None, dtype=None, **kwargs):
    defaults = {
        "dim": shape,
        "mean": torch.zeros(shape),
    }
    defaults.update(kwargs)
    for key in defaults:
        if isinstance(defaults[key], torch.Tensor):
            defaults[key] = defaults[key].to(device=device, dtype=dtype)
    return bg.NormalDistribution(**defaults)


def _make_truncated_normal_distribution(shape, device=None, dtype=None, **kwargs):
    defaults = {
        "mu": torch.zeros(shape),
        "sigma": torch.ones(shape),
    }
    defaults.update(kwargs)
    for key in defaults:
        if isinstance(defaults[key], torch.Tensor):
            defaults[key] = defaults[key].to(device=device, dtype=dtype)

        if isinstance(defaults[key], float) or (isinstance(defaults[key], int) and not isinstance(defaults[key], bool)):
            defaults[key] = (
                torch.ones(shape, device=device, dtype=dtype) * defaults[key]
            )

    return bg.TruncatedNormalDistribution(**defaults)


DISTRIBUTION_FACTORIES = {
    bg.UniformDistribution: _make_uniform_distribution,
    bg.NormalDistribution: _make_normal_distribution,
    bg.TruncatedNormalDistribution: _make_truncated_normal_distribution,
}
