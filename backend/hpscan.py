"""HP Scanner class for performing scan operations via eSCL protocol.
This is a modified version of the original hpscan.py for the web backend.
Textual-specific imports have been removed.
"""
from pathlib import Path
import bs4
import datetime
import requests
import socket
import time

from schema import scan_xml_schema


class HPScanner:
    """Class of HP Scanner to perform scan operations.
    """
    def __init__(self, dict_scan_config: dict = None) -> None:
        """Initializes the HPScanner class with the given IP address.

        Args:
            dict_scan_config: Dictionary containing scan configuration parameters.
        """
        self.dict_scan_config = dict_scan_config or {}
        
        
        if self.dict_scan_config.get("ip"):
            self.host = self.dict_scan_config["ip"]
            if not self.check_printer(self.host):
                print(f"Error. couldn't connect to the printer. please check the ip: {self.host}")
            try:
                print(f"Connecting to {self.host}...")
                self.session = requests.Session()
            except requests.exceptions.RequestException as e:
                print(f"Error establishing session: {e}")
                return

    def check_printer(self, ip: str) -> bool:
        """check if printer can establish connection at port 9100

        Args:
            ip: Given IP address of the printer.

        Returns:
            returns True if connection is established, else False.
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

    def get_capabilities(self):
        """Checks the capabilities of the printer model.

        Returns:
            object of class Capability with attributes
        """
        URL_SCANNER_CAPABILITY  = f'http://{self.host}/eSCL/ScannerCapabilities'
        response = self.session.get(URL_SCANNER_CAPABILITY)
        soup = bs4.BeautifulSoup(response.text,"xml")
        class Capability:       
            make_and_model = soup.find('pwg:MakeAndModel').text
            serial_number = soup.find('pwg:SerialNumber').text
            manufacturer = soup.find('scan:Manufacturer').text
            firmware_version = soup.find('pwg:Version').text
            platen_info = soup.find('scan:Platen')
            min_width = int(platen_info.find('scan:MinWidth').text)
            max_width = int(platen_info.find('scan:MaxWidth').text)
            min_height = int(platen_info.find('scan:MinHeight').text)
            max_height = int(platen_info.find('scan:MaxHeight').text)
            color_modes = [mode.text for mode in platen_info.find_all('scan:ColorMode')]
            document_formats = [format.text for format in platen_info.find_all('pwg:DocumentFormat')]
            supported_resolutions = [int(res.find('scan:XResolution').text) for res in platen_info.find_all('scan:DiscreteResolution')]
        return Capability()

    def print_capabilities(self) -> object:
        """prints the capabilities of the printer model.
        """
        capabilities = self.get_capabilities()
        print(f"Make and Model: {capabilities.make_and_model}")
        print(f"Serial Number: {capabilities.serial_number}")
        print(f"Manufacturer: {capabilities.manufacturer}")
        print(f"Firmware Version: {capabilities.firmware_version}")
        print()
        print(f"Min/Max Width: {capabilities.min_width}/{capabilities.max_width}")
        print(f"Min/Max Height: {capabilities.min_height}/{capabilities.max_height}")
        print(f"Supported Color Modes: {', '.join(capabilities.color_modes)}")
        print(f"Supported Resolutions: {', '.join([str(x) for x in capabilities.supported_resolutions])}")
        return capabilities

        
    def get_job(self,retry_count: int = 0):
        """gets the job uri of the current job.
        If no job is found, it retries for 5 times. If still no job is found, it returns None.

        Args:
            retry_count: Retry counter for recursive calls.

        Returns:
            job uri of the current job.
        """
        URL_SCANNER_STATUS = f'http://{self.host}/eSCL/ScannerStatus'
        response = self.session.get(URL_SCANNER_STATUS)
        soup = bs4.BeautifulSoup(response.text,"xml")
        job_infos = soup.find_all('scan:JobInfo')
        for job_info in job_infos:
            job_uri = job_info.find('pwg:JobUri').text.strip()
            job_state = job_info.find('pwg:JobState').text.strip()
            if job_state == "Processing":
                return job_uri
        if retry_count < 5:
            time.sleep(0.2)
            return self.get_job(retry_count=retry_count+1)
 
    def perform_scan(self) -> None:
        """performs the scan with the given parameters.

        Args:
            dpi: quality of the scan. Defaults to 0.
            h: height of the scan. Defaults to 0.
            w: width of the scan. Defaults to 0.
            cm: colour scheme. Defaults to "RGB24".
            pdf: output format of file. Defaults to False.
            out_file_name: name of the file. Defaults to None.
        """
        URL_CREATE_SCAN = f'http://{self.host}/eSCL/ScanJobs'
        capability = self.get_capabilities()
        height = self.dict_scan_config.get("height") if self.dict_scan_config.get("height") else capability.max_height
        width = self.dict_scan_config.get("width") if self.dict_scan_config.get("width") else capability.max_width
        xdpi, ydpi  = 300, 300
        format = "application/pdf" if self.dict_scan_config.get("pdf") else "image/jpeg"  
        colormode = self.dict_scan_config.get("colormode") if self.dict_scan_config.get("colormode") in capability.color_modes else capability.color_modes[-1]
        print(f"scan parameters:: h: {height}, w: {width}, dpi: {xdpi}, cm: {colormode}, format: {format}")
        data = scan_xml_schema.format(
            height = height,
            width = width,
            xdpi = xdpi,
            ydpi = ydpi,
            format = format,
            colormode = colormode
        )
        res = self.session.post(URL_CREATE_SCAN,data = data)
        if res.status_code != 201:
            http_code = -1
            description = "scanner may be busy. please wait."
            try:
                soup = bs4.BeautifulSoup(res.text,"xml")
                http_code = soup.find("httpcode").text
                description = soup.find("description").text
            except:
                pass
            print(f"scan error! code: {http_code}, reason: {description}.")
            time.sleep(5)
            raise Exception(f"Scan error: {http_code} - {description}")
        job = self.get_job()
        if job:
            url = f'http://{self.host}{job}/NextDocument'
            print("scan started. please wait...")
            data = self.session.get(url).content
            
            #create file name
            file_name = self.dict_scan_config.get("output") if self.dict_scan_config.get("output") else datetime.datetime.now().strftime("SCAN_%Y%m%d_%H%M%S")
            file_name += ".pdf" if self.dict_scan_config.get("pdf") else ".jpg"
            
            #set output directory
            file_path = Path(self.dict_scan_config.get("output_dir")) if self.dict_scan_config.get("output_dir") else Path.cwd()
            file_name = file_path.joinpath(file_name)
            file = Path(file_name)
            suffix = 1
            temp = file
            while file.exists():
                file = temp.parent.joinpath(f"{temp.stem}_{suffix}{temp.suffix}")
                suffix += 1
            file.write_bytes(data)
            print(f"scan complete. saved {file}")
            return str(file)
    
    def get_ip_address(self):
        """gets ip addresse of the machine.

        Returns:
            ip address of the machine.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address
        except socket.error as e:
            return
