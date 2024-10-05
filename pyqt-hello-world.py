import sys
import matplotlib.pyplot as plt
import seaborn as sns
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hello World App")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and set layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Add label
        self.label = QLabel("Hello, World!", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.label)

        # Add horizontal container for text input
        horizontal_container = QWidget(self)
        horizontal_layout = QHBoxLayout()
        horizontal_container.setLayout(horizontal_layout)
        main_layout.addWidget(horizontal_container)

        # Add label and text input to horizontal container
        input_label = QLabel("Enter your name:", self)
        horizontal_layout.addWidget(input_label)
        self.text_input = QLineEdit(self)
        horizontal_layout.addWidget(self.text_input)

        # Connect text input to label update
        self.text_input.textChanged.connect(self.on_text_input)

        # Add button to update graph
        self.update_button = QPushButton("Update Graph", self)
        self.update_button.clicked.connect(self.plot_graph)
        main_layout.addWidget(self.update_button)

        # Add matplotlib figure
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        main_layout.addWidget(self.toolbar)

        # Plot initial graph
        self.plot_graph()

    def on_text_input(self):
        text = self.text_input.text()
        self.label.setText(f"Hello, {text}!")

    def plot_graph(self):
        self.figure.clear()
        data = sns.load_dataset("iris")
        self.ax = self.figure.add_subplot(111)
        sns.scatterplot(
            data=data, x="sepal_length", y="sepal_width", hue="species", ax=self.ax
        )
        self.canvas.draw()

    def wheelEvent(self, event):
        print("wheel event")
        if event.angleDelta().y() > 0:
            self.zoom(1.2)
        else:
            self.zoom(0.8)

    def zoom(self, scale_factor):
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2

        new_width = (xlim[1] - xlim[0]) * scale_factor
        new_height = (ylim[1] - ylim[0]) * scale_factor

        self.ax.set_xlim([x_center - new_width / 2, x_center + new_width / 2])
        self.ax.set_ylim([y_center - new_height / 2, y_center + new_height / 2])
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
