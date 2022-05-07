import argparse
from rich.progress import Progress
from programmer import Programmer

if   __name__ == '__main__':
  parser = argparse.ArgumentParser(prog="Programmer", description="Serial Programmer for the AT89Sxx series of microcontrollers")
  parser.add_argument('port', metavar='<PORT>', default='/dev/ttyUSB0', type=str, help="Serial Port destination")
  parser.add_argument('file', metavar='<HEXFILE>', type=open, help="Hex File source")
  parser.add_argument('--version', action='version', version='%(prog)s 0.1')
  args = parser.parse_args()
  print(f"Programmer")
  print(f"Source Hex File: {args.file.name}")
  print(f"Destination Serial Port: {args.port}")
  
  programmer = Programmer()
  
  programmer.setSerialPort(args.port)
  programmer.setHexFile(args.file)

  filestats = programmer.analyzeFile()
  print(f"File Information:")
  print(filestats)

  devstats = programmer.analyzeDevice()
  print("Device Information:")
  print(devstats)

  usage = filestats['size']/devstats['ROM'] * 100
  print(f"ROM Usage: {usage:.2}%")
  if(usage > 100):
    print("Program is too large. Bigger than ROM")
    exit()
  
  with Progress() as progress:
    task = progress.add_task("Sending File", total=filestats['size'])
    def bar(percent: float):
      progress.advance(task)
    programmer.sendProgram(onUpdate=bar)
    print(f"")
