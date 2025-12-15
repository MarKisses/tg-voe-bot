class EmptyDisconnectionSchedule(Exception):
    """Exception for handling when no disconnection schedule's present"""
    
    def __init__(self, message):
        super().__init__(message)