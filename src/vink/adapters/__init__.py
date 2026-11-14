"""Adapters: concrete implementations of ports.

All I/O and third-party SDK usage lives here. Each adapter translates between
an external system and the domain, and converts library exceptions into
:mod:`vink.domain.errors`. Only :mod:`vink.bootstrap` should import adapters.
"""
