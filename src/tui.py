import socket
import re

from textual.app import App, ComposeResult
from textual.containers import Container, Grid, HorizontalGroup, VerticalGroup
from textual.widgets import Header, Footer, Button, Label, Input, Select, Static, Switch, ProgressBar, ListView, ListItem, DirectoryTree
from textual import on, work
from textual.worker import Worker, WorkerState, get_current_worker
from textual.message import Message

from datetime import datetime

import hpscan

# --- Define a custom message for scan completion (optional but good practice) ---
class ScanComplete(Message):
    """Custom message to signal scan completion."""
    def __init__(self, success: bool, result: any, error: Exception | None) -> None:
        self.success = success
        self.result = result
        self.error = error
        super().__init__()
        
class SearchComplete(Message):
    def __init__(self, success: bool, printers: list, error: Exception = None) -> None:
        self.success = success
        self.printers = printers
        self.error = error
        super().__init__()
        

class Printer(Static):
    """Printer widget to handle scanning operations."""
    def __init__(self, dict_scan_config, paper_format) -> None:
        
        """Initializes the Printer class with the given scan configuration.

        Args:
            dict_scan_config (dict): Dictionary containing scan configuration parameters.
        """
        super().__init__()
        # Make a copy to avoid modifying the original dict shared with the App
        self.dict_scan_config = dict_scan_config.copy() 
        self.paper_format = paper_format
        
        self.printers = [] # List to store found printers
        self._scan_worker: Worker | None = None # To keep track of the worker
        self._search_worker: Worker | None = None # To keep track of the worker
    
    def compose(self) -> ComposeResult:
        """Compose the printer

        Yields:
            Button: Button to inititate the scan
        """
        yield Grid(
            HorizontalGroup(
                VerticalGroup(
                    Label("Printer IP:", classes="printer_label"),
                    Input(
                        f"{self.dict_scan_config['ip']}",
                        classes="printer_input",
                        id="printer_ip_input",
                    ),
                ),
                VerticalGroup(
                    Label("DPI:", classes="printer_label"),
                    Input(
                        f"{self.dict_scan_config['dpi']}",
                        classes="printer_input",
                        id="dpi_input",
                    ),
                ),
                VerticalGroup(
                    Label("Format:", classes="printer_label"),
                    Select.from_values(
                        self.paper_format,
                        value="A4", # Set default value
                        classes="printer_input",
                        id="format_select",
                    ),
                ),
                VerticalGroup(
                    Label("Dateiname:", classes="printer_label"),
                    Input(
                        f"{self.dict_scan_config['output']}",
                        classes="printer_input",
                        id="output_input",
                    ),
                ),
                # TODO: Add logic for bulk scan
                # Don't forget to change grid if added in hpscantui.tcss
                # VerticalGroup(
                #     Label("Bulk Scan:", classes="printer_label"),
                #     Switch(
                #         name="Bulk Scan",
                #         id="bulk_scan_switch",
                #         classes="printer_input",
                #         value=False, # Set default value
                #     )
                # ),
                VerticalGroup(
                    Button(
                        "Scan",
                        classes="printer_input",
                        id="btn_start_scan",
                        variant="primary",
                    ),
                    # Use disabled state and text change instead of two buttons
                    Button(
                        "Scanning...",
                        classes="printer_input",
                        id="btn_scanning",
                        variant="success", # Different variant maybe?
                        disabled=True,
                    ),
                ), id="scan_grid"
            ),
            
            HorizontalGroup(
                VerticalGroup(
                    DirectoryTree("/", id="output_dir_tree", classes="directory_tree"),
                    id="output_dir_tree_group"
                ),
                VerticalGroup(
                    Label("Path:", classes="printer_label"),
                    Input(
                        f"{self.dict_scan_config['output_dir']}",
                        classes="printer_input",
                        id="output_dir_input",
                    ), id="output_dir_input_group"
                ),id="path_grid"
            ),
            id="printer_grid" # Added ID for easier querying if needed
        )

    def _update_scan_buttons(self, scanning: bool) -> None:
        """Helper to toggle scan button visibility/state."""
        self.query_one("#btn_start_scan", Button).display = not scanning
        self.query_one("#btn_scanning", Button).display = scanning
        
        
    @on(Input.Changed, "#printer_ip_input") # Target the specific input
    def on_ip_changed(self, event: Input.Changed) -> None:
        """Handles the IP address change event."""
        self.dict_scan_config["ip"] = event.value
        self.log(f"IP address set to {event.value}")
    
    @on(Input.Changed, "#dpi_input") # Target the specific input
    def on_dpi_changed(self, event: Input.Changed) -> None:
        """Handles the DPI change event."""
        try:
            dpi_value = int(event.value)
            if dpi_value <= 0:
                raise ValueError("DPI must be a positive integer.")
            self.dict_scan_config["dpi"] = dpi_value
            self.log(f"DPI set to {dpi_value}")
        except ValueError as e:
            self.app.notify(
                f"Invalid DPI value: {e}", title="Input Error", severity="error"
            )
            self.log.error(f"Invalid DPI input: {event.value} - {e}")
        
    @on(Select.Changed, "#format_select") # Target the specific select
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handles the selection change event for the format select."""
        selected_format = event.value
        # Default to A4 if something unexpected happens
        height, width = 3508, 2480 
        if selected_format == "A4":
            height, width = 3508, 2480
        elif selected_format == "A5":
            height, width = 2480, 1748
        elif selected_format == "Letter":
            height, width = 3300, 2550
        
        self.dict_scan_config["height"] = height
        self.dict_scan_config["width"] = width
        self.log(f"Format set to {selected_format}: H={height}, W={width}")


    @on(Input.Changed, "#output_input") # Target the specific switch
    def on_filename_changed(self, event: Switch.Changed) -> None:
        """Handles the filename change event."""
        self.dict_scan_config["output"] = event.value
        self.log(f"Filename set to {event.value}")


    @on(Switch.Changed, "#bulk_scan_switch") # Target the specific switch
    def on_bulk_scan_changed(self, event: Switch.Changed) -> None:
        """Handles the bulk scan switch change event."""
        self.dict_scan_config["bulk"] = event.value
        self.log(f"Bulk Scan set to {event.value}")
    
    @on(DirectoryTree.DirectorySelected, "#output_dir_tree") # Target the specific directory tree
    def on_output_dir_changed(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handles the output directory change event."""
        self.query_one("#output_dir_input", Input).value = str(event.path)
        self.dict_scan_config["output_dir"] = event.path
        self.log(f"Output directory set to {event.path}")
        
    @on(Input.Changed, "#output_dir_input") # Target the specific input
    def on_output_dir_input_changed(self, event: Input.Changed) -> None:
        """Handles the output directory input change event."""
        self.dict_scan_config["output_dir"] = event.value
        self.log(f"Output directory input changed to {event.value}")        

    @on(Button.Pressed, "#btn_start_scan") # Target the specific button
    async def start_scan_button_pressed(self, event: Button.Pressed) -> None:
        """Starts Scan worker with the current parameters."""
        
        # Prevent starting if already scanning
        if self._scan_worker is not None and not self._scan_worker.is_finished:
             self.log.warning("Scan already in progress.")
             return

        # --- Read current values from inputs ---
        try:
            self.dict_scan_config["ip"] = self.query_one(
                "#printer_ip_input", Input
            ).value
            # Ensure DPI is an integer
            dpi_value = self.query_one("#dpi_input", Input).value
            if not dpi_value.isdigit():
                 raise ValueError("DPI must be a whole number.")
            self.dict_scan_config["dpi"] = int(dpi_value)
            # Format/dimensions are updated by on_select_changed
            # Update output filename for uniqueness
            self.dict_scan_config["output"] = self.query_one("#output_input", Input).value
            # self.dict_scan_config["bulk"] = self.query_one("#bulk_scan_switch", Switch).value

        except ValueError as e:
            self.app.notify(
                f"Invalid input: {e}", title="Input Error", severity="error"
            )
            self.log.error(f"Input validation failed: {e}")
            return
        except Exception as e:
            # Catch potential query errors if widgets aren't found (shouldn't happen here)
            self.app.notify(
                f"Error reading inputs: {e}", title="Input Error", severity="error"
            )
            self.log.error(f"Failed to read inputs: {e}")
            return
        # --- End reading inputs ---

        self.log.info(f"Starting scan with config: {self.dict_scan_config}")
        self._update_scan_buttons(scanning=True)
        # Run the worker
        self._scan_worker = self.scan()
    
        
    @work(exclusive=True, thread=True, exit_on_error=False)
    def scan(self)->None:
        """Scan function to perform scan operation in a worker thread."""
        worker = get_current_worker()
        # Pass a copy of the config to the scanner instance
        scanner_config = self.dict_scan_config.copy()
        
        hpscanner = hpscan.HPScanner(scanner_config)
        
        scan_result = None
        error = None
        success = False
        

        try:
            if not worker.is_cancelled:
                # Perform the blocking scan operation IN the worker thread
                self.log.info("Worker calling hpscanner.perform_scan()") # Use self.log
                
                
                scan_result = hpscanner.perform_scan()
                scanner_config = self.dict_scan_config.copy()
        
                 
                # Assuming perform_scan returns something useful or None on success
                # And raises an exception on failure.
                success = True
                self.log.info(f"hpscanner.perform_scan() completed. Result: {scan_result}")

        except Exception as e:
            self.log.error(f"Exception during scan worker: {e}", exc_info=True) # Log exception info
            error = e
        
        # Post a message back to the widget on the main thread
        # This is generally preferred over relying solely on worker state return value
        # as it allows sending more complex data and specific error info.
        self.post_message(ScanComplete(success, scan_result, error))
    
# Handle the custom message from the worker
    def on_scan_complete(self, message: ScanComplete) -> None:
        """Handles the completion message from the scan worker."""
        self.log.info(f"Received ScanComplete message. Success: {message.success}")
        self._update_scan_buttons(scanning=False) # Reset buttons regardless of outcome

        if message.success:
            self.log.info(f"Scan successful. Result: {message.result}")
            # Optionally notify success
            self.app.notify("Scan completed successfully!", title="Scan Finished")
            # Process the result if needed (e.g., display file path)
        else:
            error_message = f"Scan failed: {message.error}"
            self.log.error(error_message)
            # Notify the user about the failure
            self.app.notify(error_message, title="Scan Error", severity="error")
            
        self._scan_worker = None # Clear the worker reference


    # You might still want on_worker_state_changed for general logging or unhandled errors
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes (logs state)."""
        # This will log transitions like starting, running, success, error, cancelled
        self.log.info(f"Worker {event.worker.name} state changed: {event.state}")
        
        # Handle unexpected worker errors that didn't result in ScanComplete message
        if event.state == WorkerState.ERROR:
             # Ensure buttons are reset even if ScanComplete wasn't sent
             self._update_scan_buttons(scanning=False)
             self.log.error(f"Unhandled worker error: {event.worker.error}", exc_info=event.worker.error)
             self.app.notify(f"Scan worker failed unexpectedly: {event.worker.error}", title="Worker Error", severity="error")
             self._scan_worker = None # Clear the worker reference

    def show_capabilities(self, capabilities):
        """Display printer capabilities in a dialog or notification."""
        # This could be a modal dialog or a simple notification
        # For simplicity, we'll just log it for now
        self.log.info(f"Printer Capabilities: {capabilities}")
        # Update the capabilities container with the information
        capabilities_text = self.app.query_one("#capabilities_text", Static)
        capabilities_text.update(
            f"Make and Model: {capabilities.make_and_model}\n"
            f"Serial Number: {capabilities.serial_number}\n"
            f"Manufacturer: {capabilities.manufacturer}\n"
            f"Firmware Version: {capabilities.firmware_version}\n\n"
            f"Min/Max Width: {capabilities.min_width}/{capabilities.max_width}\n"
            f"Min/Max Height: {capabilities.min_height}/{capabilities.max_height}\n"
            f"Supported Color Modes: {', '.join(capabilities.color_modes)}\n"
            f"Supported Resolutions: {', '.join([str(x) for x in capabilities.supported_resolutions])}"
        )
        
    @work(exclusive=True, thread=True, exit_on_error=False)
    def search_network(self) -> None:
        """Search for printers in the network."""
        printers = []
        try:
            self.log.info("Searching for printers...")
            machine_ip = self.get_ip_address()
            _ip = re.findall(r"\d+\.\d+\.\d+\.", machine_ip)[0]
            ip_range = [_ip + str(i) for i in range(2, 255) if _ip + str(i) != machine_ip]
            progress_bar = self.app.query_one("#progress_bar", ProgressBar)
            progress_bar.update(total=len(ip_range),progress=0)   
            
            for ip in ip_range:
                progress_bar.advance(1)
                if self.check_printer(ip):
                    printers.append(ip)
            self.post_message(SearchComplete(success=True, printers=printers))
        except Exception as e:
            self.log.error(f"Error searching for printers: {e}", exc_info=True)
            self.post_message(SearchComplete(success=False, printers=[], error=e))
        
    # def show_printers(self):
    #     """Display found printers in the printer container."""
    #     printer_text = self.app.query_one("#printer_text", Static)
    #     if self.printers:
    #         printer_text.update("\n".join(self.printers))
    #     else:
    #         printer_text.update("No printers found.")
    
    def show_printers(self):
        """Display found printers in the printer container."""
        printer_list = self.app.query_one("#printer_list", ListView)
        printer_list.clear()
        if self.printers:
            for p in self.printers:
                printer_list.append(ListItem(Label(f"{p}")))
        else:
            printer_list.append(ListItem(Label("No printer found")))
            
    
    def on_search_complete(self, message: SearchComplete) -> None:
        """Handles the completion of the search.

        Args:
            message (SearchComplete): Message containing the result of the search.
        """
        if message.success:
            self.printers = message.printers
            self.log.info(f"Found {len(message.printers)} printers.")
            
        else:
            print(f"Error: {message.error}")
        
        self.show_printers()

    def get_ip_address(self):
        """gets ip addresse of the machine.

        Returns:
            str: ip address of the machine.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address
        except socket.error as e:
            return
        
    def check_printer(self, ip: str) -> bool:
        """check if printer can establish connection at port 9100

        Args:
            ip (str): Given IP address of the printer.

        Returns:
            bool: returns True if connection is established, else False.
        """
        try:
            for i in range(10):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                result = sock.connect_ex((ip, 9100))
                if result == 0:
                    return True 
                sock.close()
        except:
            return False
    
    @on(ListView.Selected, "#printer_list")
    def select_printer(self, event: ListView.Selected) -> None:
        """Handles the selection of a printer from the list."""
        self.log.info(f"ListView.Selected event triggered: {event}")
        selected_item = event.item
        selected_label = selected_item.query_one(Label)
        selected_value = selected_label.text  # Use `.text` instead of `.content`
        
        self.log.info(f"Selected printer: {selected_value}")
        self.scan_config = self.app.dict_scan_config
        self.scan_config["ip"] = selected_value
        
        

            
class hpscantui(App):
    """Main application class for the HP Scan CLI TUI."""
    
    dict_scan_config = {
                    "ip":"192.168.13.93",
                    "height":3508,
                    "width":2480,
                    "dpi":300,
                    "colormode":"RGB24",
                    "pdf":True,
                    "output":f"{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "output_dir":"/scandir",
                    "bulk":False}
    
    paper_format = ["A4", "A5", "Letter"]
    
    App.dict_scan_config = dict_scan_config
    App.paper_format = paper_format

    CSS_PATH = "hpscantui.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "search", "Search printers"),
        ("c", "capability", "Printer Capabilities"),
    ]
    
    def compose(self):
        yield Header()
        yield Footer()
        yield Container(
           
            Label("HP Scan CLI", id="title"),
            Printer(self.dict_scan_config, self.paper_format),

            
            id="main_container"

        )
        yield Container(
            # Static("No printers found yet.", id="printer_text", classes="printer_search"),
            ListView(
                ListItem(Label("No printer found. Please check if printer is turned on and search again.")),
                id="printer_list"
            ),
            ProgressBar(total=150, show_eta=True, id="progress_bar", classes="printer_search"),
            id="printer_container",
        )
        yield Container(
            Label("Printer Capabilities", id="capabilities_label"),
            Static("No capabilities loaded yet.", id="capabilities_text"),
            id="capabilities_container",
        )
        
    def action_quit(self):
        self.exit()
        
    async def action_search(self) -> None:
        """Search for printers in the network."""
        printer_widget = self.query_one(Printer)
        printer_widget.search_network()
        
    
    def action_capability(self):
        """Get printer capabilities."""
        hpscanner = hpscan.HPScanner(self.dict_scan_config)
        self.capabilities = hpscanner.get_capabilities()
        
        printer_widget = self.query_one(Printer)
        printer_widget.show_capabilities(self.capabilities)
