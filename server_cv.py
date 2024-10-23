#!/usr/bin/env python3

from typing import Optional, Union
import socket
import sys
import cv2
import pickle
import numpy as np
import struct
from numpy.typing import NDArray

def recv_all(conn: socket.socket, n: int) -> Optional[bytes]:
    """
    Helper function to receive exactly n bytes from a connection.
    
    Args:
        conn: Network socket connection
        n: Number of bytes to receive
        
    Returns:
        bytes or None if connection closed
    """
    data = bytearray()
    while len(data) < n:
        try:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        except socket.error as e:
            print(f"Socket error while receiving: {e}")
            return None
    return bytes(data)

def receive_frame(conn: socket.socket) -> Optional[NDArray]:
    """
    Reliably receive a video frame over a network connection.
    
    Args:
        conn: Network socket connection
        
    Returns:
        numpy array representing the frame or None if error
    """
    try:
        # Get the message size first (4 bytes)
        size_data = recv_all(conn, 4)
        if size_data is None:
            return None
            
        size = struct.unpack('>L', size_data)[0]
        
        # Now get the actual frame data
        frame_data = recv_all(conn, size)
        if frame_data is None:
            return None
            
        # Deserialize the frame
        frame: NDArray = pickle.loads(frame_data)
        return frame
        
    except (socket.error, pickle.UnpicklingError) as e:
        print(f"Error receiving frame: {e}")
        return None

def main() -> None:
    # Connection settings
    HOST: str = '10.0.0.74'
    PORT: int = 8089
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    print('Socket created')
    
    try:
        server_socket.bind((HOST, PORT))
        print('Socket bind complete')
        
        server_socket.listen(10)
        print('Socket now listening')
        
        print(f'Waiting for connection on {HOST}:{PORT}...')
        conn, addr = server_socket.accept()
        print(f'Connected to {addr}')
        
        while True:
            # Receive frame
            frame = receive_frame(conn)
            
            if frame is None:
                print("No frame received, connection might be closed")
                break
            
            # Display the frame
            cv2.imshow('Frame', frame)
            
            # Break loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quit command received")
                break
                
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        print("Cleaning up...")
        try:
            conn.close()
        except NameError:
            pass  # Connection wasn't established
        server_socket.close()
        cv2.destroyAllWindows()
        print("Cleanup complete")

if __name__ == "__main__":
    main()

