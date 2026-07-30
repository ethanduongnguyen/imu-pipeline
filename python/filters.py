import numpy as np
from abc import ABC, abstractmethod
from collections import deque
import scipy.signal as signal

class BaseFilter(ABC):
    @abstractmethod
    def update(self, measurement: np.ndarray) -> np.ndarray:
        pass
    
    @abstractmethod
    def reset(self):
        pass
    
    @abstractmethod
    def getMetadata(self) -> dict:
        pass
    
    def __call__(self, measurement):
        return self.update(measurement)
    
    # Allow filters to be applied for offline processing, i.e. data from a loaded CSV file
    def apply(self, data: np.ndarray) -> np.ndarray:
        self.reset()
        is_1d = data.ndim == 1
        if is_1d:
            data_2d = data[:, np.newaxis]
        else:
            data_2d = data
            
        filtered_results = []
        for sample in data_2d:
            filtered_results.append(self.update(sample))
        
        result = np.array(filtered_results)
        return result.flatten() if is_1d else result 
    
class MovingAverage(BaseFilter):
    def __init__(self, window_size: int = 5, num_channels: int = 3):
        self.window_size = window_size
        self.num_channels = num_channels
        self.buffer = deque(maxlen=window_size)
        self.reset()
        
    def reset(self):
        self.buffer.clear()
        
    def update(self, measurement: np.ndarray) -> np.ndarray:
        self.buffer.append(measurement)
        return np.mean(self.buffer, axis = 0)

    def getMetadata(self) -> dict:
        return {
            "filter_type": "Moving Average",
            "window_size": self.window_size,
            "num_channels": self.num_channels
        }

class ExponentialMovingAverage(BaseFilter):
    def __init__(self, alpha: float = 0.9):
        self.alpha = alpha
        self.prev_ema = None
        self.reset()
        
    def reset(self):
        self.prev_ema = None
        
    def update(self, measurement: np.ndarray) -> np.ndarray:
        if self.prev_ema is None:
            self.prev_ema = np.array(measurement, dtype=float)
            return self.prev_ema
        
        ema = self.alpha * measurement + (1 - self.alpha) * self.prev_ema
        self.prev_ema = ema
        return ema
    
    def getMetadata(self) -> dict:
            return {
                "filter_type": "Exponential Moving Average",
                "alpha" : self.alpha
            }
            
class ZeroPhaseButterworth(BaseFilter):
    def __init__(self, cutoff_freq: float, sampling_rate: float, order: int = 4):
        self.cutoff_freq = cutoff_freq
        self.sampling_rate = sampling_rate
        self.order = order
        
        # Nyquist frequency is half the sampling rate
        nyquist = 0.5 * self.sampling_rate
        normal_cutoff = self.cutoff_freq / nyquist
        
        # Generate filter coefficients (numerator a, denominator b)
        self.b, self.a = signal.butter(self.order, normal_cutoff, btype='low', analog=False)
        
    def update(self, measurement: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Zero-phase filtering requires the entire array. Use apply() instead.")
    
    def reset(self):
        pass
    
    def apply(self, data: np.ndarray) -> np.ndarray:
        # Applies forward-backward zero-phase filter
        return signal.filtfilt(self.b, self.a, data, axis=0)
    
    def getMetadata(self) -> dict:
        return {
            "filter_type" : "Zero-Phase Butterworth",
            "cutoff_frequency" : self.cutoff_freq,
            "sampling_rate" : round(self.sampling_rate, 2),
            "order" : self.order
        }