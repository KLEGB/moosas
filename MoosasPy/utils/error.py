

class ShellError(Exception):
    def __init__(self, execution, message):
        """Initialize a new instance with execution context and message.
        
            Parameters
            ----------
            execution : any
                The execution context or environment to be stored in the instance.
            message : str
                The message string associated with the instance.
        
            Returns
            -------
            None
                This constructor does not return a value."""
        self.execution = execution
        self.message = message

    def __str__(self):
        """Return a string representation of the FileError exception.
        
        Parameters
        ----------
        self : FileError
            The instance of the FileError exception.
        
        Returns
        -------
        str
            A string in the format '{execution}: {message}', where 'execution' and 'message' 
            are attributes of the FileError instance.
        """
        return f"{self.execution}: {self.message}"


class FileError(Exception):
    def __init__(self, file):
        """
        Initialize the object with a file.
        
        Parameters
        ----------
        file : object
            The file to be assigned to the instance variable.
        
        Returns
        -------
        None
        """
        self.file = file

    def __str__(self):
        """Return a string representation of the FileError indicating the file is not a valid moosas file.
        
        Returns
        -------
        str
            A string describing the error, including the name of the invalid file.
        """
        return f"FileError, {self.file} is not a valid moosas file"

class GeometryError(Exception):
    def __init__(self,geometry,reason):
        """
        Initialize a new instance with geometry and reason attributes.
        
        Parameters
        ----------
        geometry : object
            The geometric representation or data associated with the instance.
        reason : str
            A description or explanation indicating the reason for the instance's state or creation.
        
        Returns
        -------
        None
            This constructor does not return any value.
        """
        self.geometry = geometry
        self.reason = reason

    def __str__(self):
        """Return a string representation of the TopologyError exception.
        
        Parameters
        ----------
        self : TopologyError
            The instance of the TopologyError exception to represent as a string.
            Contains attributes `geometry` and `reason` that describe the error.
        
        Returns
        -------
        str
            A formatted string describing the error in the form "GeometryError: {geometry} is invalid: {reason}".
        """
        return f"GeometryError: {self.geometry} is invalid: {self.reason}"

class TopologyError(Exception):
    def __init__(self,func,reason):
        """
        Initialize a new instance with a function and a reason.
        
        Parameters
        ----------
        func : callable
            The function to be stored in the instance.
        reason : str
            A string describing the reason associated with the function.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        self.func = func
        self.reason = reason
    def __str__(self):
        """Return a string representation of the TopologyError instance.
        
            Parameters
            ----------
            self : object
                The instance of TopologyError.
        
            Returns
            -------
            str
                A formatted string describing the error, including the function name and reason.
        """
        return f"TopologyError: {self.func}, {self.reason}"
