import numpy as np
from abc import ABC, abstractmethod
from collections import deque

class BaseFilter(ABC):
    @abstractmethod
    def update(self, measurement: np.ndarray) -> np.ndarray:
        pass
    
    @abstractmethod
    def reset(self):
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

class ExponentialMovingAverage(BaseFilter):
    def __init__(self, alpha: float = 0.9):
        self.alpha = alpha
        self.prev_ema = None
        self.reset()
        
    def reset(self):
        self.prev_ema = None
        
    def update(self, measurement: np.ndarray) -> np.ndarray:
        if self.prev_ema is None:
            self.prev_ema = np.ndarray(measurement, dtype=float)
            return self.prev_ema
        
        ema = self.alpha * measurement + (1 - self.alpha) * self.prev_ema
        self.prev_ema = ema
        return ema