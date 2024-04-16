from pypylon import pylon
from PIL import Image
import numpy as np
import os
from pathlib import Path
import uuid
import logging
from timeit import default_timer

from typing import Union

from Camera import get_camera_by_ip_address, get_camera_by_serial_number


class SimpleCameraWrapper:
    camera = None
    camera_parameter = None
    converter = None
    timeout = 1000
    settings = dict()
    _transmission_type = None
    _destination_ip = None
    _destination_port = None
    _emulate_camera = False

    def __init__(
            self,
            timeout_milliseconds: int = 1000,
            verbose: bool = False,
            **kwargs
    ):
        self.verbose = verbose
        self.set_timeout(timeout_milliseconds)
        self.set_settings(**kwargs)

    def _open_camera(self) -> bool:
        if not self._emulate_camera and (self.camera is not None) and (not self.camera.isOpen()):
            self.camera.Open()
        return True

    def __exit__(self, exc_type, exc_value, traceback):
        if self.camera is not None and not self._emulate_camera:
            self.camera.Close()

    def _print(self, info: Union[str, dict], method: str):
        if self.verbose:
            if isinstance(info, dict):
                msg = "(" + ", ".join([f"{ky}={val}" for ky, val in info.items() if val]) + ")"
            else:
                msg = "(): " + info
            print(f"BaslerPylonCameraWrapper.{method}" + msg)
            logging.debug(msg)

    def set_timeout(self, timeout_milliseconds: int = None) -> bool:
        # verbose: print input
        info = {"timeout_milliseconds": timeout_milliseconds}
        self._print(info, "set_timeout")

        if isinstance(timeout_milliseconds, int) and timeout_milliseconds > 0:
            self.timeout = timeout_milliseconds
            return True
        return False

    def set_settings(
            self,
            serial_number: int = None,
            ip_address: str = None,
            emulate_camera: bool = False,
            timeout: int = None,
            transmission_type: str = None,
            destination_ip_address: str = None,
            destination_port: int = None
    ) -> bool:
        info = {
            "serial_number": serial_number,
            "ip_address": ip_address,
            "emulate_camera": emulate_camera,
            "timeout": timeout,
            "transmission_type": transmission_type,
            "destination_ip_address": destination_ip_address,
            "destination_port": destination_port
        }
        self._print(info, "set_settings")

        self.create_camera(
            ip_address=ip_address,
            serial_number=serial_number,
            emulate_camera=emulate_camera
        )
        self.set_timeout(timeout_milliseconds=timeout)
        self.set_streaming_parameters(
            transmission_type=transmission_type,
            destination_ip=destination_ip_address,
            destination_port=destination_port
        )
        return True

    def create_camera(
            self,
            serial_number: int = None,
            ip_address: str = None,
            emulate_camera: bool = False
    ) -> bool:
        # verbose: print input
        info = {
            "serial_number": serial_number,
            "ip_address": ip_address,
            "emulate_camera": emulate_camera
        }
        self._print(info, "create_camera")

        camera_parameter = None
        if emulate_camera:
            # emulate camera
            camera_parameter = dict()
            self._emulate_camera = True

        elif ip_address and serial_number:
            raise ValueError(
                "Too many options. "
                "Serial number and IP address were specified but only one of both was expected as input."
            )
        elif serial_number:
            # find camera by serial number
            camera_parameter = {"serial_number": serial_number}
        elif ip_address:
            # find camera by IP address
            camera_parameter = {"ip_address": ip_address}

        if camera_parameter is not None and self.camera_parameter != camera_parameter:
            self._print(f"camera_parameter={camera_parameter}", "create_camera")
            self.camera = self._create_camera(**camera_parameter)
            self._set_converter()
            return True

        self._print(f"No camera created", "create_camera")
        return False

    # @staticmethod
    def _create_camera(
            self,
            serial_number: int = None,
            ip_address: str = None
    ) -> pylon.InstantCamera:
        self._print(f"serial_number={serial_number}, ip_address={ip_address}", "_create_camera")
        # create camera object
        if serial_number:
            # find camera by serial number
            cam_info = get_camera_by_serial_number(serial_number)
            cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam_info))
        elif ip_address:
            # find camera by IP address
            cam = get_camera_by_ip_address(ip_address.strip("'").strip('"'))
        else:
            self._print("Emulating a camera.", "_create_camera")
            os.environ['PYLON_CAMEMU'] = "1"
            cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

        return cam

    def set_streaming_parameters(
            self,
            transmission_type: str = None,
            destination_ip: str = None,
            destination_port: int = None
    ) -> bool:
        # verbose: print input
        info = {
            "transmission_type": transmission_type,
            "destination_ip": destination_ip,
            "destination_port": destination_port
        }
        self._print(info, "set_streaming_parameters")

        # set parameters (store locally)
        if transmission_type:
            self._transmission_type = transmission_type
        if destination_ip:
            self._destination_ip = destination_ip
        if destination_port:
            self._destination_port = destination_port

        if (self.camera is None) and (self._transmission_type or self._destination_ip or self._destination_port):
            raise ValueError("Camera not yet created!")
        elif self._transmission_type or self._destination_ip or self._destination_port:
            self._open_camera()
            self.__set_streaming_parameters(self.camera)
        return True

    def __set_streaming_parameters(self, cam: pylon.InstantCamera) -> bool:
        if cam.IsOpen() and cam.StreamGrabber and not self._emulate_camera:
            if self._transmission_type and cam.StreamGrabber.TransmissionType.GetValue() != self._transmission_type:
                if self.verbose:
                    self._print(f"Set TransmissionType from {cam.StreamGrabber.TransmissionType.GetValue()} "
                                f"to {self._transmission_type}", "__set_streaming_parameters")

                cam.StreamGrabber.TransmissionType.SetValue(self._transmission_type)

            if self._destination_ip and cam.StreamGrabber.DestinationAddr.GetValue() != self._destination_ip:
                if self.verbose:
                    self._print(f"Set DestinationAddr from {cam.StreamGrabber.DestinationAddr.GetValue()} "
                                f"to {self._destination_ip}", "__set_streaming_parameters")

                cam.StreamGrabber.DestinationAddr.SetValue(self._destination_ip)

            if self._destination_port and cam.StreamGrabber.DestinationPort.GetValue() != self._destination_port:
                if self.verbose:
                    self._print(f"Set DestinationPort from {cam.StreamGrabber.DestinationPort.GetValue()} "
                                f"to {self._destination_port}", "__set_streaming_parameters")

                cam.StreamGrabber.DestinationPort.SetValue(self._destination_port)

            return True
        return False

    def _get_image(self, frame: pylon.GrabResult):
        if self.converter is None:
            return frame.GetArray()
        else:
            return self.converter.Convert(frame).GetArray()

    def _set_converter(self):
        # no image conversion necessary for grayscale images (mono-8-type)
        if self.camera.IsCameraLink() and self.camera.PixelFormat.GetValue().find('RGB') >= 0:
            # set up converter to get opencv's bgr format
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def grab_image(self, exposure_time_microseconds: int = 40000, timeout: int = None) -> Union[np.ndarray, None]:
        # verbose: print input
        info = {"exposure_time_microseconds": exposure_time_microseconds}
        self._print(info, "grab_image")

        if self.camera is None:
            raise ValueError("Camera not yet created!")

        if timeout:
            self.set_timeout(timeout_milliseconds=timeout)

        return self._grab_image(exposure_time_microseconds)

    def _grab_image(self, exposure_time_microseconds: int) -> Union[np.ndarray, None]:
        t0 = default_timer()
        # open camara session
        self._open_camera()
        cam = self.camera
        # set exposure time
        if exposure_time_microseconds:
            cam.ExposureTimeAbs.SetValue(exposure_time_microseconds)
        # set stream parameters
        self.__set_streaming_parameters(cam)
        # grab image
        frame = cam.GrabOne(self.timeout)
        # convert if necessary
        img = self._get_image(frame)
        t1 = default_timer()
        self._print(f"Execution took {t1 - t0:.5} seconds.", "_grab_image")
        return img

    def save_image(
            self,
            filename: Union[str, Path] = None,
            file_extension: str = ".webp",
            **kwargs
    ) -> Path:
        img = self.grab_image(**kwargs)

        if filename is None:
            filename = Path().cwd()
        else:
            # ensure pathlib object
            filename = Path(filename)

        if filename.is_dir():
            # create random file name
            filename = (filename / str(uuid.uuid4())).with_suffix(file_extension)

        # save image #
        Image.fromarray(img).save(filename.as_posix(), lossless=True)
        return filename

    def _get_device_info(self):
        self._open_camera()
        return self.camera.GetDeviceInfo()

    def get_device_info(self) -> dict:
        cam_info = self._get_device_info()

        info = {
            "name": cam_info.GetModelName(),
            "IP": cam_info.GetIpAddress(),
            "mac": cam_info.GetMacAddress()
        }
        return info

    def get_device_name(self) -> str:
        cam_info = self._get_device_info()
        return cam_info.GetFullName()
