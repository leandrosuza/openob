"""Custom exceptions for OpenOB"""


class OpenOBError(Exception):
    """Base exception for all OpenOB errors"""
    pass




class AuthenticationError(OpenOBError):
    """Authentication and authorization errors"""
    pass




class ValidationError(OpenOBError):
    """Data validation errors"""
    pass




class ConfigurationError(OpenOBError):
    """Configuration and environment errors"""
    pass




class DatabaseError(OpenOBError):
    """Database and repository errors"""
    pass




class TradingError(OpenOBError):
    """Trading and order errors"""
    pass




class MarketDataError(OpenOBError):
    """Market data and candle errors"""
    pass




class TimeoutError(OpenOBError):
    """Operation timeout errors"""
    pass
