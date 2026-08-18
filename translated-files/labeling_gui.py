import sys
import numpy as np
import scipy.io as sio
import json
from pathlib import Path
import PyQt6.QtCore
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox)
import pyqtgraph as pg
from process_trial import process_trial

class LabelingApp(QMainWindow):
    def __init__(self, filebase_name: str, trial_subfolder: str):
        super().__init__()
        self.filebase_name = filebase_name
        self.trial_subfolder = trial_subfolder
        
        self.setWindowTitle("Interactive IMU and Vicon Labeler")
        self.resize(1200, 800)
        
        self.data_imu = None
        self.vicon_joints = None
        self.vicon_knee_vel = None
        self.alignment_ids = None
        self.t_imu = None
        self.t_vicon = None
        self.imu_label = None
        self.nuc_predictions = None
        
        # Marker tracking for point-and-click labeling
        self.boundary_indices = []
        self.pending_index = None
        self.finished = False
        
        # Explicit handles to the drawn InfiniteLine objects, keyed by index
        # for committed boundaries, so a specific line can be removed
        # directly (e.g. on undo) instead of relying on a full clear/redraw.
        self.boundary_lines = {}
        self.pending_line = None
        
        # History of committed labeling actions, for undo. Each entry is a
        # dict: {'type': 'label' | 'finish', 'start_idx', 'end_idx', 'label_value'}
        self.action_history = []
        
        # Main widgets and layouts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Plotting canvas set up
        plot_layout = QVBoxLayout()
        
        # Plot main data
        self.plot_canvas = pg.PlotWidget(title="Time Series Data")
        self.plot_canvas.setLabel('left', 'Amplitude')
        self.plot_canvas.showGrid(x=True, y=True)
        self.plot_canvas.addLegend()
        
        self.plot_canvas.scene().sigMouseClicked.connect(self.on_mouse_click)
        
        # Plot label data
        self.label_canvas = pg.PlotWidget(title='Current Labels')
        self.label_canvas.setLabel('bottom', 'Time')
        self.label_canvas.setLabel('left', 'Class (0-5)')
        self.label_canvas.setYRange(-0.5, 5.5, padding=0)
        self.label_canvas.showGrid(x=True, y=True)
        
        # Link the x-axis of both graphs
        self.label_canvas.setXLink(self.plot_canvas)
        
        plot_layout.addWidget(self.plot_canvas, stretch=3)
        plot_layout.addWidget(self.label_canvas, stretch=1)
        
        main_layout.addLayout(plot_layout, stretch=4)
        
        # Sidebar layout
        sidebar_layout = QVBoxLayout()
        
        # Data Management
        data_title = QLabel("<b>Data Management</b>")
        sidebar_layout.addWidget(data_title)
        
        self.load_btn = QPushButton(f"Load '{self.filebase_name}' Trial Data [Ctrl + L]")
        self.load_btn.setShortcut(QKeySequence("Ctrl+L"))
        self.load_btn.clicked.connect(self.load_trial_data)
        sidebar_layout.addWidget(self.load_btn)
        
        sidebar_layout.addWidget(QLabel("<b>Toggle Sensor View</b>"))
        self.view_selector = QComboBox()
        self.view_selector.addItems([
            "Vicon-IMU Index Alignment",
            "Shank Omegas",
            "Torso Acceleration",
            "Torso Omega",
            "Shank Accelerations",
            "Height, Joint Angles, and Pitch",
            "Knee Angular Velocity"
        ])
        
        self.view_selector.currentIndexChanged.connect(self.plot_real_data)
        self.view_selector.setEnabled(False) # Disabled until data loads
        sidebar_layout.addWidget(self.view_selector)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar_layout.addWidget(line)
        
        self.status_label = QLabel("Load a trial to begin.")
        self.status_label.setWordWrap(True)
        sidebar_layout.addWidget(self.status_label)
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar_layout.addWidget(line2)
                
        # Labeling controls
        label_title = QLabel("<b>Labeling Controls</b>")
        sidebar_layout.addWidget(label_title)
        
        self.states = {
            0: "Standing", 1: "Squatting", 2: "One-Legged Kneeling (R)", 3: "Move Up", 4: "Move Down", 5: "Doubled-Legged Kneeling", 6: "Stepping", 7: "One-Legged Kneeling (L)"
        }
        
        for val, name in self.states.items():
            btn = QPushButton(f"{val}: {name} [{val}]")
            btn.setShortcut(QKeySequence(str(val)))
            btn.clicked.connect(lambda checked, v=val: self.apply_label(v))
            sidebar_layout.addWidget(btn)
        
        self.undo_btn = QPushButton("Undo Last Boundary [Ctrl+Z]")
        self.undo_btn.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_btn.clicked.connect(self.undo_last_boundary)
        sidebar_layout.addWidget(self.undo_btn)
            
        finish_title = QLabel("<b>Finish Trial</b>")
        sidebar_layout.addWidget(finish_title)
        sidebar_layout.addWidget(QLabel("Labels the last region through the final frame: "))
        
        self.finish_label_selector = QComboBox()
        for val,name in self.states.items():
            self.finish_label_selector.addItem(f"{val}: {name}", userData = val)
        sidebar_layout.addWidget(self.finish_label_selector)
        
        self.finish_btn = QPushButton("Finish Trial (label to end) [F]")
        self.finish_btn.setShortcut(QKeySequence("F"))
        self.finish_btn.clicked.connect(self.finish_trial)
        sidebar_layout.addWidget(self.finish_btn)
        
        # Add sidebar to main layout
        sidebar_layout.addStretch()
        main_layout.addLayout(sidebar_layout, stretch = 1)
    
    def load_trial_data(self):
        """
        Runs the data pipeline and plots the result
        """
        self.load_btn.setText("Processing...")
        QApplication.processEvents() # Force UI to update
        
        try:
            # Call pipeline as done in process_trial.py
            # Example: 
            # self.data_imu = process_trial(
            #         filename_base = "std2KN1"
            #         trial_subfolder = "0727_Ethan_data"
            #     )
            self.data_imu, self.vicon_joints, self.vicon_knee_vel, self.alignment_ids, self.t_imu, self.t_vicon, self.nuc_predictions = process_trial(
                self.filebase_name,
                self.trial_subfolder
            )
            
            # self.t_imu = np.asarray(self.t_imu).reshape(-1)
            # self.t_vicon = np.asarray(self.t_vicon).reshape(-1)
            
            # Initialize the empty label array (zeros)
            num_frames = self.data_imu.shape[0]
            self.imu_label = np.zeros(num_frames, dtype=int)
            
            # Reset boundary tracking
            self.boundary_indices = [0]
            self.pending_index = None
            self.finished = False
            self.boundary_lines = {}
            self.pending_line = None
            self.action_history = []
            
            self.view_selector.setEnabled(True)
            self.plot_real_data()
            self.update_label_plot()
            self.update_status_label()
             
            self.load_btn.setText(f"Trial '{self.filebase_name}' loaded successfully!")
            self.load_btn.setEnabled(False) # Disable button after loading
            
        except Exception as e:
            self.load_btn.setText("Error loading data.")
            print(f"Error: {e}")
    
    def on_mouse_click(self, event):
        """
        Converts left mouse clicks to draw boundaries
        """
        if self.t_imu is None or event.button() != PyQt6.QtCore.Qt.MouseButton.LeftButton:
            return
        
        if self.finished:
            print({"Trial is already finished. Reload to make further edits."})
            return
        
        vb = self.plot_canvas.plotItem.vb
        
        if self.plot_canvas.sceneBoundingRect().contains(event.scenePos()):
            mouse_point = vb.mapSceneToView(event.scenePos())
            clicked_time = mouse_point.x()
            
            raw_idx = np.searchsorted(self.t_imu, clicked_time)
            idx = int(np.clip(raw_idx, 0, len(self.t_imu) - 1))
            
            # Remove the previous pending line (if any) and draw the new one directly,
            # rather than clearing/redrawing the whole canvas.
            if self.pending_line is not None:
                self.plot_canvas.removeItem(self.pending_line)
                self.pending_line = None
            
            self.pending_index = idx
            self.pending_line = self.add_marker_line(self.t_imu[idx], committed=False)
            
            self.update_status_label()
            
    def add_marker_line(self, x_time, committed = True):
        """
        Draws a vertical dashed line at the clicked marker. Returns the created
        line object so callers can track and later remove it directly.
        """
        if committed:
            pen = pg.mkPen(color='w', width=2, style=PyQt6.QtCore.Qt.PenStyle.DashLine)
        else: 
            pen = pg.mkPen(color=(255,165,0), width=2, style=PyQt6.QtCore.Qt.PenStyle.SolidLine)
        
        line = pg.InfiniteLine(pos=x_time, angle=90, movable=False, pen=pen)
        self.plot_canvas.addItem(line)
        return line
        
    def plot_real_data(self):
        """
        Dynamically plots sensors based on the dropdown selection
        """
        self.plot_canvas.clear()
        if self.data_imu is None or self.vicon_joints is None:
            print("Error loading IMU Data or Vicon Joints. Exiting...")
            return
        
        current_view = self.view_selector.currentText()
        
        # Pens for plotting
        pen_red = pg.mkPen(color=(255,0,0), width=1)
        pen_cyan = pg.mkPen(color=(0,255,255), width=1)
        pen_yellow = pg.mkPen(color=(255,0,255), width=1)
        pen_pink = pg.mkPen(color=(255,192,203), width=1)
        pen_blue = pg.mkPen(color=(0,0,255), width=1)
        pen_orange = pg.mkPen(color=(255,165,0), width=1)
        
        if current_view == "Vicon-IMU Index Alignment":
            self.plot_canvas.setLabel('bottom', 'VICON Index')
            self.plot_canvas.setLabel('left', 'IMU Index')
            if self.alignment_ids is not None:
                id_vicon, id_imu = self.alignment_ids
                self.plot_canvas.plot(
                    id_vicon, id_imu,
                    pen=None,
                    symbol='o',
                    symbolSize=3,
                    symbolBrush=(0, 255, 255),
                    name="Alignment Points"
                )
        else:
            self.plot_canvas.setLabel('bottom', 'Time (s)')
            self.plot_canvas.setLabel('left', 'Amplitude')
        
            if current_view == "Shank Omegas":
                leftshank_omega = self.data_imu[:, 13]
                rightshank_omega = self.data_imu[:, 22]
                
                self.plot_canvas.plot(self.t_imu, leftshank_omega, name="Left Shank Omega", pen=pen_cyan)
                self.plot_canvas.plot(self.t_imu, rightshank_omega, name="Right Shank Omega", pen=pen_red)
            
            elif current_view == "Torso Acceleration":
                torso_acc_x = self.data_imu[:, 0]
                torso_acc_y = self.data_imu[:, 1]
                torso_acc_z = self.data_imu[:, 2]
                
                self.plot_canvas.plot(self.t_imu, torso_acc_x, name="Torso Accel X", pen = pen_cyan)
                self.plot_canvas.plot(self.t_imu, torso_acc_y, name="Torso Accel Y", pen = pen_red)
                self.plot_canvas.plot(self.t_imu, torso_acc_z, name="Torso Accel Z", pen = pen_yellow)
                
            elif current_view == "Torso Omega":
                torso_omega_x = self.data_imu[:, 3]
                torso_omega_y = self.data_imu[:, 4]
                torso_omega_z = self.data_imu[:, 5]
                
                self.plot_canvas.plot(self.t_imu, torso_omega_x, name="Torso Omega X", pen = pen_cyan)
                self.plot_canvas.plot(self.t_imu, torso_omega_y, name="Torso Omega Y", pen = pen_red)
                self.plot_canvas.plot(self.t_imu, torso_omega_z, name="Torso Omega Z", pen = pen_yellow)
                
            elif current_view == "Shank Accelerations":
                left_acc_x = self.data_imu[:, 9]
                left_acc_y = self.data_imu[:, 10]
                left_acc_z = self.data_imu[:, 11]
                right_acc_x = self.data_imu[:, 18]
                right_acc_y = self.data_imu[:, 19]
                right_acc_z = self.data_imu[:, 20]
                
                self.plot_canvas.plot(self.t_imu, left_acc_x, name="Left Shank Accel X", pen=pen_cyan)
                self.plot_canvas.plot(self.t_imu, left_acc_y, name="Left Shank Accel Y", pen=pen_red)
                self.plot_canvas.plot(self.t_imu, left_acc_z, name="Left Shank Accel Z", pen=pen_yellow)
                self.plot_canvas.plot(self.t_imu, right_acc_x, name="Right Shank Accel Z", pen=pen_pink) 
                self.plot_canvas.plot(self.t_imu, right_acc_y, name="Right Shank Accel Z", pen=pen_blue) 
                self.plot_canvas.plot(self.t_imu, right_acc_z, name="Right Shank Accel Z", pen=pen_orange) 
                
            elif current_view == "Height, Joint Angles, and Pitch":
                torso_height = self.vicon_joints[:,20]
                left_knee = self.vicon_joints[:,0]
                right_knee = self.vicon_joints[:,5]
                IMU_left_thigh = self.data_imu[:,16]
                IMU_right_thigh = self.data_imu[:,25]
                
                self.plot_canvas.plot(self.t_vicon, torso_height, name="Torso Height", pen=pen_yellow)
                self.plot_canvas.plot(self.t_vicon, left_knee, name="Left Knee Joint Angle", pen=pen_cyan)
                self.plot_canvas.plot(self.t_vicon, right_knee, name="Right Knee Joint Angle", pen=pen_red)
                self.plot_canvas.plot(self.t_imu, IMU_left_thigh, name="Left Thigh Pitch", pen=pen_orange)
                self.plot_canvas.plot(self.t_imu, IMU_right_thigh, name="Right Thigh Pitch", pen=pen_pink)
                
            elif current_view == "Knee Angular Velocity":
                if self.vicon_knee_vel is not None:
                    self.plot_canvas.plot(self.t_vicon, self.vicon_knee_vel[:, 0], name="Left Knee Velocity", pen=pen_cyan)
                    self.plot_canvas.plot(self.t_vicon, self.vicon_knee_vel[:, 1], name="Right Knee Velocity", pen=pen_red)
                    
                    # Threshold lines at +/- 20 deg/s
                    pen_thresh = pg.mkPen(color=(200, 200, 200), width=1.5)
                    self.plot_canvas.addItem(pg.InfiniteLine(pos=20, angle=0, movable=False, pen=pen_thresh))
                    self.plot_canvas.addItem(pg.InfiniteLine(pos=-20, angle=0, movable=False, pen=pen_thresh))
            
            # clear() wipes all previously tracked line objects, so rebuild the
            # tracking dict/reference fresh alongside redrawing them.
            self.boundary_lines = {}
            for idx in self.boundary_indices:
                if 0 <= idx < len(self.t_imu):
                    self.boundary_lines[idx] = self.add_marker_line(self.t_imu[idx], committed=True)
            
            self.pending_line = None
            if self.pending_index is not None:
                self.pending_line = self.add_marker_line(self.t_imu[self.pending_index], committed=False)
        
        self.plot_canvas.autoRange()
        
    def apply_label(self, label_value):
        """
        Applies selected label to frames bounded by the mouse clicks
        """
        if self.imu_label is None:
            print("Please load data first.")
            return
        
        if self.finished:
            print("Trial is finished. Reload to make further edits.")
            return
        
        if self.pending_index is None:
            print("Click a boundary on the graph first.")
        
        start_idx = self.boundary_indices[-1]
        end_idx = self.pending_index
        
        if end_idx <= start_idx:
            print(f"New boundary must be after the previous boundary.")
            return
        
        # Update array
        self.imu_label[start_idx: end_idx] = label_value
        
        # Remove the pending line -- it's about to become a committed one
        if self.pending_line is not None:
            self.plot_canvas.removeItem(self.pending_line)
            self.pending_line = None
        
        # Commit pending boundary
        self.boundary_indices.append(end_idx)
        self.pending_index = None
        self.action_history.append({
            'type': 'label',
            'start_idx': start_idx,
            'end_idx': end_idx,
            'label_value': label_value
        })
        
        # Draw the committed line directly and track its handle
        self.boundary_lines[end_idx] = self.add_marker_line(self.t_imu[end_idx], committed=True)
        
        self.update_label_plot()
        self.update_status_label()
        
        print(f"Applied label {label_value} ({self.states[label_value]}) to frames {start_idx}-{end_idx}")
        
    def finish_trial(self):
        if self.imu_label is None:
            print("Please load data first.")
            return
        
        if self.finished:
            print("Trial already finished. Reload to make further edits.")
            return
        
        label_value = self.finish_label_selector.currentData()
        
        start_idx = self.boundary_indices[-1]
        last_idx = len(self.imu_label) - 1
        
        if start_idx > last_idx:
            print("Nothing left to label; trial already covers every frame.")
            return
        
        self.imu_label[start_idx:last_idx + 1] = label_value
        
        # Remove the pending line -- it's about to become a committed one
        if self.pending_line is not None:
            self.plot_canvas.removeItem(self.pending_line)
            self.pending_line = None
        
        self.boundary_indices.append(last_idx)
        self.pending_index = None
        self.finished = True
        self.action_history.append({
            'type': 'finish',
            'start_idx': start_idx,
            'end_idx': last_idx,
            'label_value': label_value
        })
        # Draw the final committed line directly and track its handle
        self.boundary_lines[last_idx] = self.add_marker_line(self.t_imu[last_idx], committed=True)
        
        self.update_label_plot()
        self.update_status_label()
        
        print(f"Applied label {label_value} ({self.states[label_value]}) to frames {start_idx}--{last_idx}"
              f" (end of trial) Trial fully labeled.")
        
        # Saving trial and label into '.mat' file
        BASE_DIR = Path(__file__).resolve().parent.parent
        SAVE_DIR = BASE_DIR / 'data' / 'processed' / self.trial_subfolder
        
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        
        SAVE_FILE_PATH = SAVE_DIR / f"{self.filebase_name}_labeled.mat"
        JSON_FILE_PATH = SAVE_DIR / f"{self.filebase_name}_metadata.json"
        
        mat_data = {
            'Data_IMU': self.data_imu,
            'IMU_label': self.imu_label.reshape(-1, 1)
        }
        
        try:
            sio.savemat(SAVE_FILE_PATH, mat_data)
            self.status_label.setText(f"Trial fully labeled and saved to {SAVE_FILE_PATH}.")
            
            boundary_times = [float(self.t_imu[idx]) for idx in self.boundary_indices]
            metadata = {
                "filebase_name": self.filebase_name,
                "trial_subfolder": self.trial_subfolder,
                "total_frames": len(self.imu_label),
                "boundary_indices": self.boundary_indices,
                "boundary_times_sec": boundary_times
            }
            
            with open(JSON_FILE_PATH, "w") as json_file:
                json.dump(metadata, json_file, indent=4)
                
            print(f"Successfully saved labeled '.mat' file to: {SAVE_FILE_PATH}")
            print(f"Successfully saved metadata to: {JSON_FILE_PATH}")
                
        except Exception as e:
            print(f"Error saving {self.filebase_name} file: {e}")
            self.status_label.setText("Error saving file. Check console.")
        
    def undo_last_boundary(self):
        """
        Reverts the most recently committed boundary (from apply_label or
        finish_trial), restoring imu_label for that region back to 0 and
        removing the boundary. Can be called repeatedly to step back through
        multiple committed boundaries. 
        """
        if self.imu_label is None:
            print("Please load data first.")
            return
        
        if not self.action_history:
            print("Nothing to undo.")
            return
        
        # Discard any uncommitted pending click/line -- undo targets committed boundaries
        if self.pending_line is not None:
            self.plot_canvas.removeItem(self.pending_line)
            self.pending_line = None
        self.pending_index = None
        
        action = self.action_history.pop()
        start_idx = action['start_idx']
        end_idx = action['end_idx']
        
        if action['type'] == 'finish':
            self.imu_label[start_idx:end_idx + 1] = 0
            self.finished = False
        else:
            self.imu_label[start_idx:end_idx] = 0
        
        # Explicitly remove the exact line object this action created
        line_to_remove = self.boundary_lines.pop(end_idx, None)
        if line_to_remove is not None:
            self.plot_canvas.removeItem(line_to_remove)
        
        # Remove the boundary this action committed
        if self.boundary_indices and self.boundary_indices[-1] == end_idx:
            self.boundary_indices.pop()
        
        # Restore the undone boundary as a pending line so it can be immediately relabeled
        self.pending_index = end_idx
        self.pending_line = self.add_marker_line(self.t_imu[end_idx], committed=False)
        
        self.update_label_plot()
        self.update_status_label()
        
        print(f"Undid label {action['label_value']} ({self.states[action['label_value']]}) "
              f"for frames {start_idx}-{end_idx}")
        
    def update_status_label(self):
        """
        Keeps sidebar status text in synch with current boundary state
        """
        if self.t_imu is None:
            self.status_label.setText("Load a trial to begin.")
            return
        
        if self.finished:
            self.status_label.setText("Trial fully labeled through the last frame.")
            return
        
        last_boundary_idx = self.boundary_indices[-1]
        last_boundary_time = self.t_imu[last_boundary_idx]
        
        if self.pending_index is not None:
            pending_time = self.t_imu[self.pending_index]
            self.status_label.setText(
                f"Region start: t={last_boundary_time: .2f}s (index {last_boundary_idx}) \n"
                f"Pending boundary: t={pending_time:.2f}s (index {self.pending_index}).\n"
                f"Pick a label to apply it."
            )
        else:
            self.status_label.setText(
                f"Region start: t={last_boundary_time:.2f}s (index {last_boundary_idx}).\n"
                f"Click a new boundary on the graph."
            )
        
    def update_label_plot(self):
        """
        Creates staircase plot of current imu_label array.
        """
        self.label_canvas.clear()
        
        # Plot NUC prediction as a faint dashed grey line for reference
        if hasattr(self, 'nuc_predictions') and self.nuc_predictions is not None:
            pen_nuc = pg.mkPen(color=(150, 150, 150), width=1.5, style=PyQt6.QtCore.Qt.PenStyle.DashLine)
            self.label_canvas.plot(self.t_imu, self.nuc_predictions, pen=pen_nuc, name="NUC Prediction")
        
        if self.imu_label is not None:
            pen = pg.mkPen(color=(255,0,0), width=2)
            self.label_canvas.plot(self.t_imu, self.imu_label, pen=pen)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LabelingApp(
        filebase_name = 'Activity_detect',
        trial_subfolder = '0817_data'
    )
    window.show()
    sys.exit(app.exec())