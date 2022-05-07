
class Serial:
  baudrate = 115200

  def __init__(self, port: str, baudrate: int) -> None:
    print("Warning: Using FAKE Serial stub")
  
  def write(self, byte: int):
    pass
