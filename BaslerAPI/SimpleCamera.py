from pypylon import pylon
from PIL import Image
from pathlib import Path
import uuid

from typing import Union


class BaslerCamera:
    def __init__(self, ip_address=None, serial_number=None, timeout=1000, transmission_type='Unicast',
                 destination_ip=None, destination_port=None):
        self.ip_address = ip_address
        self.serial_number = serial_number
        self.timeout = timeout
        self.transmission_type = transmission_type
        self.destination_ip = destination_ip
        self.destination_port = destination_port
        self.camera = None

    def connect(self):
        # Create a camera object
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

        if self.ip_address:
            # Connect to the camera using IP address
            cam_info = pylon.CInstantCameraInfo().CreateByIpAddress(self.ip_address)
            # cam_info = get_camera_by_ip_address(self.ip_address)
        elif self.serial_number:
            # Connect to the camera using serial number
            cam_info = pylon.CInstantCameraInfo().CreateBySerialNumber(self.serial_number)
            # cam_info = get_camera_by_serial_number(self.serial_number)
        self.camera.Open(cam_info)

        # Set parameters if provided
        if self.timeout:
            self.camera.GrabTimeout = self.timeout
        if self.transmission_type and self.destination_ip and self.destination_port:
            self.camera.StartGrabbing(
                pylon.GrabStrategy_LatestImageOnly,
                pylon.GrabLoop_ProvidedByInstantCamera
            )

    def take_photo(self):
        if self.camera is None:
            raise RuntimeError("Camera is not connected. Call connect() method first.")

        # Wait for a grab result
        grab_result = self.camera.RetrieveResult(self.timeout, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            # Convert the grabbed image to PIL Image object
            img = grab_result.Array
            image = Image.fromarray(img)
            return image
        else:
            raise RuntimeError("Failed to grab an image")

    def disconnect(self):
        if self.camera is not None:
            self.camera.StopGrabbing()
            self.camera.Close()
            self.camera = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def save_image(
            self,
            filename: Union[str, Path] = None,
            file_extension: str = ".webp",
            **kwargs
    ) -> Path:
        img = self.take_photo()

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

# Example usage:
if __name__ == "__main__":
    # Create camera instance with IP address
    camera = BaslerCamera(ip_address='192.168.0.10', timeout=500)

    # Connect to the camera
    camera.connect()

    # Take a photo
    photo = camera.take_photo()

    # Display the photo
    photo.show()

    # Disconnect from the camera
    camera.disconnect()
