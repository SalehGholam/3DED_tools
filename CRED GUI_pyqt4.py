# -*- coding: utf-8 -*-
"""
All tilts will be done in a thread and log will be updated.

Created on Thu Oct 19 00:20:12 2023
@author: Saleh @ EMAT
"""

import PyQt4.QtGui as qtw
from PyQt4.QtGui import QDoubleValidator
from PyQt4.QtCore import QLocale, QThread, pyqtSignal, Qt
import os
import temscript as ts
import sys
import numpy as np
import time
import datetime
import yaml
from functools import partial

class MyWindow(qtw.QWidget):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.init_tem(virtual=True) # virtual microscope
#        self.init_tem(virtual=False) # real microscope
        self.init_ui()
        
    def init_tem(self, virtual=True):
        if virtual:        
            self.myTem = ts.NullMicroscope()
        else:
            self.myTem = ts.Microscope()
            self.instrument = ts.GetInstrument()  
            self.projection = self.instrument.Projection
    
    def init_ui(self):
        self.setWindowTitle('3DED_CRED')
        self.main_layout = qtw.QVBoxLayout(self)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        #%% directory entries
        layout_dir = qtw.QHBoxLayout(self)

        label_dir = qtw.QLabel('Main Directory:')
        layout_dir.addWidget(label_dir)

        self.lineEdit_dir = qtw.QLineEdit(self)
        layout_dir.addWidget(self.lineEdit_dir)
        self.lineEdit_dir.setText(os.getcwd())
        
        self.button_dir = qtw.QPushButton('...', self)
        layout_dir.addWidget(self.button_dir)
        self.main_layout.addLayout(layout_dir)
        
#        self.worker_thread = WorkerThread()
#        self.worker_thread.folder_selected.connect(self.on_folder_selected)
        self.button_dir.clicked.connect(lambda:self.run_func_in_workerThread(self.select_directory))
        #%% parameters for the experiment
        layout_params = qtw.QHBoxLayout(self)
        params = ['Dataset Name', 'C2 Aperture Size (um)', 'Camera Speed (fps)',
                  'Starting Angle', 'Final Angle', 'Tilt Speed (deg/s)']
        self.params = {}
        setValues = {'Starting Angle':-35, 'Final Angle':35, 'Tilt Speed (deg/s)':0.5}
        
        self.groupBox_report = qtw.QGroupBox('Info for Report')
        layout_group1 = qtw.QGridLayout()
        self.groupBox_report.setLayout(layout_group1)
        for i, p in enumerate(params[:3]):
            label_temp = qtw.QLabel(p)
            lineEdit_temp = qtw.QLineEdit()
            self.params[p] = lineEdit_temp
            i_r = i * 2
            layout_group1.addWidget(label_temp, i_r, 0)
            layout_group1.addWidget(lineEdit_temp, i_r, 1)
            
        self.groupBox_params = qtw.QGroupBox('Tilt Parameters')
        layout_group2 = qtw.QGridLayout()
        self.groupBox_params.setLayout(layout_group2)
        for i, p in enumerate(params[3:6]):
            label_temp = qtw.QLabel(p)
            widget_param = qtw.QDoubleSpinBox()
            self.params[p] = widget_param
            i_r = i * 2
            layout_group2.addWidget(label_temp, i_r, 0)
            layout_group2.addWidget(widget_param, i_r, 1)

        self.params['Starting Angle'].setRange(-76, 76)
        self.params['Starting Angle'].setSingleStep(5)
        self.params['Starting Angle'].setValue(setValues['Starting Angle'])
        self.params['Final Angle'].setRange(-76, 76)
        self.params['Final Angle'].setSingleStep(5)
        self.params['Final Angle'].setValue(setValues['Final Angle'])
        self.params['Tilt Speed (deg/s)'].setRange(0.1, 15)
        self.params['Tilt Speed (deg/s)'].setSingleStep(0.5)
        self.params['Tilt Speed (deg/s)'].setValue(setValues['Tilt Speed (deg/s)'])
        double_validator = QDoubleValidator()
        double_validator.setLocale(QLocale.system())
        self.params['Camera Speed (fps)'].setValidator(double_validator)

        layout_params.addWidget(self.groupBox_report)
        layout_params.addWidget(self.groupBox_params)
        self.main_layout.addLayout(layout_params)
        #%% pre-tilt options
        layout_preExperiment = qtw.QHBoxLayout(self)
#        self.checkbox_pre_tilt = qtw.QCheckBox('Pre-tilt at Start')
#        layout_preExperiment.addWidget(self.checkbox_pre_tilt)

        layout_preTilt = qtw.QLabel('Pre-Tilt Angle', self)
        layout_preExperiment.addWidget(layout_preTilt)
        
        self.spin_preTilt = qtw.QDoubleSpinBox(self)
        self.spin_preTilt.setRange(0, 5)
        self.spin_preTilt.setSingleStep(1)
        self.spin_preTilt.setValue(2)
        layout_preExperiment.addWidget(self.spin_preTilt)
        
        self.main_layout.addLayout(layout_preExperiment)

        label_delay = qtw.QLabel('Tilt Delay (sec)')
        layout_preExperiment.addWidget(label_delay)
        
        self.spinbox_delay = qtw.QSpinBox()
        self.spinbox_delay.setRange(0, 15)
        self.spinbox_delay.setSingleStep(5)
        self.spinbox_delay.setValue(5)
        layout_preExperiment.addWidget(self.spinbox_delay)
        
        layout_endOptions = qtw.QHBoxLayout()
        label_endOptions = qtw.QLabel('At the end:')
        self.checkbox_blankAtEnd = qtw.QCheckBox('Blank the beam')
        self.checkbox_lowerScreen = qtw.QCheckBox('Lower the Screen')
        self.checkbox_fullReport = qtw.QCheckBox('Get Full Report')
        self.checkbox_fullReport.setChecked(True)
        layout_endOptions.addWidget(label_endOptions)
        layout_endOptions.addWidget(self.checkbox_blankAtEnd)
        layout_endOptions.addWidget(self.checkbox_lowerScreen)
        layout_endOptions.addWidget(self.checkbox_fullReport)
        self.main_layout.addLayout(layout_endOptions)
        #%% tilt buttons
        layout_tiltButtons = qtw.QHBoxLayout(self)
        self.button_goToStart = qtw.QPushButton('Go to Start')
        layout_tiltButtons.addWidget(self.button_goToStart)
        self.button_goToStart.clicked.connect(lambda: self.run_func_in_workerThread(self.tiltToStart))
        
        self.button_goToZero = qtw.QPushButton('Go to 0')
        layout_tiltButtons.addWidget(self.button_goToZero)
        self.button_goToZero.clicked.connect(lambda: self.run_func_in_workerThread(self.tiltToZero))
        

        self.button_goToEnd = qtw.QPushButton('Go to End')
        layout_tiltButtons.addWidget(self.button_goToEnd)
        self.button_goToEnd.clicked.connect(lambda: self.run_func_in_workerThread(self.tiltToEnd))
        
        self.main_layout.addLayout(layout_tiltButtons)
        #%% final buttons
        layout_finalButtons = qtw.QHBoxLayout()
        self.button_beamBlank = qtw.QPushButton('Beam Blank')
        self.button_beamBlank.clicked.connect(self.beam_blanker)
        
        self.button_start = qtw.QPushButton('T I L T !')
        self.button_start.clicked.connect(lambda: self.run_func_in_workerThread(self.tilt))
        
        layout_finalButtons.addWidget(self.button_beamBlank)        
        layout_finalButtons.addWidget(self.button_start)
        self.main_layout.addLayout(layout_finalButtons)
        layout_endLabels = qtw.QHBoxLayout(self)        
        label_note = qtw.QLabel('NOTE: This GUI does not acquire any image!')
        layout_endLabels.addWidget(label_note)
        self.main_layout.addLayout(layout_endLabels)
        #%% LOG label
        layout_log = qtw.QHBoxLayout()
        label_log_title = qtw.QLabel('LOG:')
        font = qtw.QFont()
        font.setBold(True)
        label_log_title.setFont(font)
        self.label_log = qtw.QLabel('')
        layout_log.addWidget(label_log_title)
        layout_log.addWidget(self.label_log, alignment=Qt.AlignLeft)
        self.main_layout.addLayout(layout_log)
#%% functions
    def tiltToStart(self):
        self.label_log.setText('tilting...')
        alpha_st_deg = float(self.params['Starting Angle'].text())
        alpha_st = np.radians(alpha_st_deg)
        alpha_preTilt_deg = float(self.spin_preTilt.text())
        alpha_preTilt = np.radians(alpha_preTilt_deg)
        if alpha_preTilt_deg >= 0.1:
            self.myTem.set_stage_position(a=alpha_st-alpha_preTilt)
            time.sleep(0.2)
        self.myTem.set_stage_position(a=alpha_st)
        self.label_log.setText('')
    
    def tiltToEnd(self):
        self.label_log.setText('tilting...')
        alpha_fi_deg = float(self.params['Final Angle'].text())
        alpha_fi = np.radians(alpha_fi_deg)
        self.myTem.set_stage_position(a=alpha_fi)
        self.label_log.setText('')
    
    def tiltToZero(self):
        self.label_log.setText('tilting...')
        self.myTem.set_stage_position(a=np.radians(-1))
        self.myTem.set_stage_position(a=0)
        self.label_log.setText('')
    
    def tilt(self):
        self.alpha_st_deg = float(self.params['Starting Angle'].text())
        self.alpha_st = np.radians(self.alpha_st_deg)
        current_alpha = np.degrees(self.myTem.get_stage_position()['a'])
        if (current_alpha - self.alpha_st_deg) >= 0.1:
            msgBox = qtw.QMessageBox()
            msgBox.setText("Current alpha is more than 0.1 deg off. Do you want to tilt to starting alpha?")
            msgBox.setWindowTitle("Initial Alpha Check")
            msgBox.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No)
            result = msgBox.exec_()
            if result == qtw.QMessageBox.Yes:
                self.tiltToStart()
        self.alpha_fi_deg = float(self.params['Final Angle'].text())
        self.alpha_fi = np.radians(self.alpha_fi_deg)
        
        self.speed = float(self.params['Tilt Speed (deg/s)'].text())
        #TODO claculation of nominal speed can be more precise
        self.speedNom = self.speed * (0.015 / 0.426)
        self.tilt_delay = int(self.spinbox_delay.text())
        for i in range(self.tilt_delay):
            self.label_log.setText('Tilt starts in %d s!' % (self.tilt_delay-i))
            time.sleep(1)
        self.label_log.setText('tilting...')
        ## temserver gives an error for an operation lasting more than 3 mins
        # expectedDuration = (self.alpha_fi_deg - self.alpha_st_deg) / self.speed
        # noSets = math.ceil(expectedDuration / 180)
        # sets = np.linspace(self.alpha_st_deg, self.alpha_fi_deg, noSets+1)
        # sets = np.radians(sets)
        tilt_limit = 180 * self.speed
        sets = np.arange(self.alpha_st_deg, self.alpha_fi_deg, tilt_limit)
        sets = sets[1:]
        sets = np.append(sets, self.alpha_fi_deg)
        sets = np.radians(sets)
        self.startTime = datetime.datetime.now().strftime("%H:%M:%S")
        tic = time.perf_counter()
        for alpha in sets:
            self.myTem.set_stage_position(a=alpha, speed=self.speedNom)
        toc = time.perf_counter()
        self.finishTime = datetime.datetime.now().strftime("%H:%M:%S")
        self.duration = toc - tic
        if self.checkbox_blankAtEnd.isChecked():
            self.beam_blanker()
        if self.checkbox_lowerScreen.isChecked():
            self.myTem.set_screen_position('DOWN')
        self.label_log.setText('Creating the report file...')
        self.create_report()
        self.label_log.setText('')
#==============================================================================
#     def start_worker_thread(self, func):
#         self.worker_thread = WorkerThread()
# #        self.worker_thread.finished.connect()
#         self.worker_thread.start()
#==============================================================================
    
    def run_func_in_workerThread(self, func, *args):
        func_to_send = partial(func, *args)
        self.worker_thread = WorkerThread(func_to_send)
        self.worker_thread.start()
#        self.worker_thread.exec_func_signal.emit(func_to_send)

    def select_directory(self):
         path_initial = os.getcwd()
         directory = qtw.QFileDialog.getExistingDirectory(None, 'Choose Directory', 
         path_initial)
         if directory:
             self.lineEdit_dir.setText(directory)

#    def on_folder_selected(self, directory):
#            self.lineEdit_dir.setText(directory)
        
    def beam_blanker(self):
        if self.myTem.get_beam_blanked():
            self.myTem.set_beam_blanked(False)
            self.button_beamBlank.setStyleSheet('background-color: #d4d0c8; color:black')
        else:
            self.myTem.set_beam_blanked(True)
            self.button_beamBlank.setStyleSheet('background-color: #ffff81; color:black')
    
    def create_report(self):
        cameraLength = self.projection.CameraLength
        datasetName = self.params['Dataset Name'].text()
        camera_speed = float(self.params['Camera Speed (fps)'].text())
        c2ap = self.params['C2 Aperture Size (um)'].text()
        realSpeed = (self.alpha_fi_deg-self.alpha_st_deg) / self.duration
        integration_perFrame = realSpeed / camera_speed
        
        if self.checkbox_fullReport.isChecked():
            try:
                microscope_state = self.myTem.get_state()
            except:
                self.projection.Mode = 1
                microscope_state = self.myTem.get_state()
        ## yaml cant handle tuples
            for key, val in microscope_state.items():
                if isinstance(val, tuple):
                    ls = []
                    for item in val:
                        ls.append(float(item))
                    microscope_state[key] = ls
        else:
            microscope_state = 'None'
        
        self.report = {"Dataset Name": datasetName,
                       "Starting Angle (deg)": self.alpha_st_deg,
                       "Final Angle (deg)": self.alpha_fi_deg,
                       "Date": datetime.date.today(), 
                       "Camera Length (m)": cameraLength, 
                       "Camera Speed (fps)" : camera_speed,
                       "Total tilt time (s)": self.duration, 
                       "Estimated Speed (deg/s)": self.speed, 
                       "Real Speed (deg/s)": realSpeed, 
                       "Integration (deg/frame)": integration_perFrame,
                       "Starting Time": self.startTime, 
                       "Finishing Time": self.finishTime,
                       "Nominal Speed": self.speedNom,
                       "C2 aperture (um)": c2ap,
                       "Microscope state": microscope_state}
        
        # report = {**report, **microscope_state}
        self.reportName = 'Report_DS_%s.txt' % datasetName
        self.pathMain = self.lineEdit_dir.text()
        print('main path:', self.pathMain)
        self.pathDataset = os.path.join(self.pathMain, datasetName)
        print('dataset path:', self.pathDataset)
        if os.path.isdir(self.pathDataset):
            msgBox = qtw.QMessageBox()
            msgBox.setText("The dataset folder exist. Do you want to overwrite it?")
            msgBox.setWindowTitle("Overwrite Report")
            msgBox.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No)
            result = msgBox.exec_()
            if result == qtw.QMessageBox.Yes:
                pass
            else:
                #TODO option to enter another dataset name
                self.report['Dataset Name'] += '_v2'
                self.pathDataset = os.path.join(self.pathMain, self.report['Dataset Name'])
        os.mkdir(self.pathDataset)
        self.write_report_file()
        
    def write_report_file(self):
        fn_report = os.path.join(self.pathDataset, self.reportName)
        # TODO check the sorting of the keys in the final report. It might not work in python 3.4
        with open(fn_report, 'w') as f:
#            yaml.dump(self.report, f, sort_keys=False, indent=4)
            yaml.dump(self.report, f, indent=4)
        
    def closeEvent(self, event):
        self.myTem.set_beam_blanked(False)
        event.accept()
        app.exit()
#%% Worker Thread
class WorkerThread(QThread):
    exec_signal = pyqtSignal(object)
    
    def __init__(self, func_received, parent=None):
        super(WorkerThread, self).__init__(parent)
        self.func_received = func_received
    
    def run(self):
        self.exec_signal.connect(self.exec_func)
        self.exec_func(self.func_received)
    
    def exec_func(self, func):
        func()
        
        
if __name__ == '__main__':
    global app
    app = 0 # kernel dies in case this line doesn't exist
    app = qtw.QApplication(sys.argv)
    window = MyWindow()
    window.show()
#    sys.exit(app.exec_())
    app.exec_()
