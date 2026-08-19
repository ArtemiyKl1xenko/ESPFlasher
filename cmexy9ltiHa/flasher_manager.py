"""
Manager for ESP32 flashing operations using esptool.
Supports all ESP32 variants and ESP8266.
"""
import sys
import subprocess
import threading
from typing import List, Optional, Callable
from models import FileEntry, FlashOperation
from esp_utils import ESPChipDetector, ESPChip, get_flash_params_for_chip


class FlasherManager:
    """Manages ESP32 flashing operations."""

    def __init__(self, on_log: Callable = None):
        """
        Initialize flasher manager.

        Args:
            on_log: Callback function to receive log messages. Signature: on_log(text: str)
        """
        self.on_log = on_log or (lambda x: None)
        self.current_process = None
        self.is_running = False
        self.detected_chip: Optional[ESPChip] = None  # Store detected chip info

    def log(self, text: str):
        """Log a message."""
        self.on_log(text)

    # ============ CHIP DETECTION ============

    def detect_chip(self, port: str, baud: int = 115200) -> str:
        """
        Detect chip type and parameters.

        Returns:
            Output from chip_id command
        """
        cmd = [sys.executable, "-m", "esptool", "--port", port, "--baud", str(baud), "chip_id"]
        self.log(f"> {' '.join(cmd)}\n")

        try:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                universal_newlines=True
            )
            output, _ = process.communicate(timeout=15)
            self.log(output)

            # Try to detect chip model
            chip = ESPChipDetector.detect_chip_model(output)
            if chip:
                self.detected_chip = chip
                self.log(f"\n[✓ Detected] {chip.name} - {chip.description}\n")
                self.log(f"  Default flash mode: {chip.default_flash_mode}\n")
                self.log(f"  Default flash freq: {chip.default_flash_freq}\n")

            return output
        except subprocess.TimeoutExpired:
            process.kill()
            error_msg = "[ERROR] Chip detection timeout\n"
            self.log(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"[ERROR] {str(e)}\n"
            self.log(error_msg)
            return error_msg

    # ============ FLASH OPERATIONS ============

    def build_write_flash_command(
        self,
        port: str,
        baud: int,
        files: List[FileEntry],
        auto_detect: bool = True,
        chip: Optional[ESPChip] = None
    ) -> Optional[List[str]]:
        """
        Build esptool write_flash command from file entries.

        Args:
            port: Serial port
            baud: Baud rate
            files: List of FileEntry objects
            auto_detect: Use auto parameters detection
            chip: Optional chip info for optimized parameters

        Returns:
            Command list or None if validation fails
        """
        if not port:
            self.log("[ERROR] Port is not selected\n")
            return None

        if not files:
            self.log("[ERROR] No files selected\n")
            return None

        cmd = [
            sys.executable, "-m", "esptool",
            "--port", port,
            "--baud", str(baud),
            "write_flash"
        ]

        # Add auto-detect parameters
        if auto_detect:
            # Use detected chip parameters if available
            if chip:
                flash_params = get_flash_params_for_chip(chip)
                cmd.extend(["--flash_mode", flash_params['flash_mode']])
                cmd.extend(["--flash_freq", flash_params['flash_freq']])
                cmd.extend(["--flash_size", flash_params['flash_size']])
            else:
                # Use fallback defaults (works for most ESP32 variants)
                cmd.extend(["--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "detect"])

        # Add all files with their addresses
        for file_entry in files:
            try:
                # Validate address format
                addr_str = file_entry.address.lower()
                if addr_str.startswith('0x'):
                    addr_int = int(addr_str, 16)
                else:
                    addr_int = int(addr_str, 16)

                cmd.append(addr_str)
                cmd.append(file_entry.path)

            except ValueError:
                self.log(f"[ERROR] Invalid address format: {file_entry.address}\n")
                return None
            except Exception as e:
                self.log(f"[ERROR] Error processing file {file_entry.path}: {e}\n")
                return None

        return cmd

    def flash(
        self,
        port: str,
        baud: int,
        files: List[FileEntry],
        auto_detect: bool = True,
        progress_callback: Callable = None,
        chip: Optional[ESPChip] = None
    ) -> bool:
        """
        Flash files to ESP32.

        Args:
            port: Serial port
            baud: Baud rate
            files: List of FileEntry objects
            auto_detect: Use auto parameters detection
            progress_callback: Callback for progress updates
            chip: Optional chip info for optimized parameters

        Returns:
            True if successful, False otherwise
        """
        cmd = self.build_write_flash_command(port, baud, files, auto_detect, chip)
        if not cmd:
            return False

        self.log(f"> {' '.join(cmd)}\n")
        self.is_running = True

        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            # Read output line by line
            for line in iter(self.current_process.stdout.readline, ''):
                if not self.is_running:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=5)
                    self.log("\n[WARNING] Flash operation cancelled\n")
                    return False

                self.log(line)
                if progress_callback:
                    progress_callback(line)

            return_code = self.current_process.wait()
            self.is_running = False

            if return_code == 0:
                self.log("\n[SUCCESS] Flash completed successfully!\n")
                return True
            else:
                self.log(f"\n[ERROR] Flash failed with code {return_code}\n")
                return False

        except Exception as e:
            self.is_running = False
            self.log(f"[ERROR] {str(e)}\n")
            return False
        finally:
            self.current_process = None

    # ============ ERASE OPERATIONS ============

    def erase_flash(self, port: str, baud: int = 115200) -> bool:
        """
        Erase entire flash memory.

        Args:
            port: Serial port
            baud: Baud rate

        Returns:
            True if successful
        """
        cmd = [
            sys.executable, "-m", "esptool",
            "--port", port,
            "--baud", str(baud),
            "erase_flash"
        ]

        self.log(f"> {' '.join(cmd)}\n")
        self.is_running = True

        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in iter(self.current_process.stdout.readline, ''):
                if not self.is_running:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=5)
                    self.log("\n[WARNING] Erase operation cancelled\n")
                    return False

                self.log(line)

            return_code = self.current_process.wait()
            self.is_running = False

            if return_code == 0:
                self.log("\n[SUCCESS] Erase completed!\n")
                return True
            else:
                self.log(f"\n[ERROR] Erase failed with code {return_code}\n")
                return False

        except Exception as e:
            self.is_running = False
            self.log(f"[ERROR] {str(e)}\n")
            return False
        finally:
            self.current_process = None

    # ============ CONTROL ============

    def stop(self):
        """Stop current operation."""
        self.is_running = False
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except:
                pass
