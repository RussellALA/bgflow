import torch
from warnings import warn
from .base import Transformer

# TODO: write docstring

__all__ = ["AffineTransformer"]


class AffineTransformer(Transformer):
    """RealNVP/NICE

    Parameters
    ----------
    is_circular : bool
        Whether this transform is periodic on [0,1].
    """

    def __init__(
        self,
        shift_transformation=None,
        scale_transformation=None,
        init_downscale=1.0,
        preserve_volume=False,
        is_circular=False,
        restrict_to_unit_interval=False,
    ):
        super().__init__()
        self._shift_transformation = shift_transformation
        self._scale_transformation = scale_transformation
        self._log_alpha = torch.nn.Parameter(torch.zeros(1) - init_downscale)
        self._preserve_volume = preserve_volume
        self._is_circular = torch.as_tensor(is_circular, dtype=torch.bool)
        if self._scale_transformation is not None:
            if self._is_circular.any():
                warn("Scaling is not compatible with periodicity. Deactivating periodicity.")
            self._is_circular = False
        self._restrict_to_unit_interval = restrict_to_unit_interval

    def _get_mu_and_log_sigma(self, x, y, *cond):
        if self._shift_transformation is not None:
            mu = self._shift_transformation(x, *cond)
        else:
            mu = torch.zeros_like(y).to(x)
        if self._scale_transformation is not None:
            alpha = torch.exp(self._log_alpha.to(x))
            log_sigma = torch.tanh(self._scale_transformation(x, *cond))
            log_sigma = log_sigma * alpha
            if self._preserve_volume:
                log_sigma = log_sigma - log_sigma.mean(dim=-1, keepdim=True)
        else:
            log_sigma = torch.zeros_like(y).to(x)
        return mu, log_sigma

    def _forward(self, x, y, **kwargs):
        context = kwargs.get("context", None)
        mu, log_sigma = self._get_mu_and_log_sigma(x, y, context)
        assert mu.shape[-1] == y.shape[-1]
        assert log_sigma.shape[-1] == y.shape[-1]
        sigma = torch.exp(log_sigma)
        dlogp = (log_sigma).sum(dim=-1, keepdim=True)
        y = sigma * y + mu
        if isinstance(self._is_circular, bool) and self._is_circular:
            y = y % 1.0
        elif isinstance(self._is_circular, torch.Tensor):
            y[..., self._is_circular] = y[..., self._is_circular] % 1.0
        return y, dlogp

    def _inverse(self, x, y, **kwargs):
        context = kwargs.get("context", None)
        mu, log_sigma = self._get_mu_and_log_sigma(x, y, context)
        assert mu.shape[-1] == y.shape[-1]
        assert log_sigma.shape[-1] == y.shape[-1]
        sigma_inv = torch.exp(-log_sigma)
        dlogp = (-log_sigma).sum(dim=-1, keepdim=True)
        y = sigma_inv * (y - mu)
        if isinstance(self._is_circular, bool) and self._is_circular:
            y = y % 1.0
        elif isinstance(self._is_circular, torch.Tensor):
            y[..., self._is_circular] = y[..., self._is_circular] % 1.0
        return y, dlogp
