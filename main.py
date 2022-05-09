import argparse
from re import sub
from sqlite3 import ProgrammingError
from rich.style import Style
from rich.progress import Progress, SpinnerColumn, DownloadColumn,TimeElapsedColumn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.columns import Columns
from rich.text import Text
from programmer import Programmer, TARGETS

if   __name__ == '__main__':
  parser = argparse.ArgumentParser(prog="Programmer", description="Serial Programmer for the AT89Sxx series of microcontrollers")
  parser.add_argument('port', metavar='<PORT>', default='/dev/ttyUSB0', type=str, help="Serial Port destination")
  parser.add_argument('file', metavar='<HEXFILE>', type=open, help="Hex File source")
  parser.add_argument('--version', action='version', version='%(prog)s 0.1')
  parser.add_argument('--target', metavar='<TARGET>', default='AT89S51', type=str, choices=(TARGETS.keys()), help="Target Model from supported list")
  args = parser.parse_args()
  console = Console()
  title = Markdown("# AT89Sxxx Programmer")
  subtitle = Markdown("#### Zenith Aerospace (@leocelente)")
  console.print(title, subtitle)
  programmer = Programmer()
  
  programmer.setSerialPort(args.port)
  programmer.setHexFile(args.file)

  filestats = programmer.analyzeFile()
  
  file_table = Table(show_header=False, header_style="bold magenta")
  file_table.add_column("key", width=12)
  file_table.add_column("value", style="bold", width=48)
  [file_table.add_row(str(k).capitalize(), str(v)) for k ,v in filestats.items()]
  file_panel = Panel.fit(file_table, title="File Information", border_style='dim')

  devstats = programmer.analyzeDevice(args.target)
  device_table = Table(show_header=False, header_style="bold magenta")
  device_table.add_column("key", width=12)
  device_table.add_column("value", style="bold", width=24)
  [ device_table.add_row(str(k).capitalize(), str(v)) for k ,v in devstats.items()]
  dev_panel = Panel.fit(device_table, title="Device Information", border_style='dim')

  usage = 101.0
  usage = filestats['size']/devstats['ROM'] * 100
  color = 'red' if usage > 75 else 'yellow' if usage > 50 else 'green'
  usage_panel = Panel.fit(f"[bold {color}] {usage:3.2f}%", title="[bold]ROM Usage", border_style='dim')
  console.print(Columns([file_panel, dev_panel, usage_panel]))

  if(usage > 100):
    console.print("[bold red]\[:skull:] - Program is too large. Bigger than ROM!")
    programmer.close()
    exit()
  
  with Progress(SpinnerColumn(),
                *Progress.get_default_columns(),
                DownloadColumn() ) as progress:
    task = progress.add_task(f"Sending [bold]{filestats['name']}", total=filestats['size'])
    def bar(percent: float):
      progress.advance(task)
    programmer.sendProgram(onUpdate=bar)
  console.print("[bold green blink] \[:100:] - Done! ")
  programmer.close()
