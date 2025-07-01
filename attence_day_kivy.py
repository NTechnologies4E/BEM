import sqlite3
import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

DB_NAME = 'attendance.db'


class AttendanceApp(App):
    def build(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()

        self.today = datetime.date.today().isoformat()  # 'YYYY-MM-DD'
        self.students = self.get_students()

        self.root_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header
        self.root_layout.add_widget(Label(text=f"Attendance for {self.today}", size_hint_y=None, height=40))

        # Input to add student
        input_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.name_input = TextInput(hint_text='Enter student name', multiline=False)
        add_button = Button(text='Add Student')
        add_button.bind(on_press=self.add_student)
        input_layout.add_widget(self.name_input)
        input_layout.add_widget(add_button)
        self.root_layout.add_widget(input_layout)

        # Attendance list area
        self.attendance_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.attendance_layout.bind(minimum_height=self.attendance_layout.setter('height'))

        scroll_view = ScrollView()
        scroll_view.add_widget(self.attendance_layout)
        self.root_layout.add_widget(scroll_view)

        # Load today's attendance
        self.load_attendance()

        return self.root_layout

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                date TEXT,
                status TEXT,
                UNIQUE(name, date)
            )
        ''')
        self.conn.commit()

    def get_students(self):
        self.cursor.execute("SELECT name FROM students ORDER BY name")
        return [row[0] for row in self.cursor.fetchall()]

    def add_student(self, instance):
        name = self.name_input.text.strip()
        if name and name not in self.students:
            try:
                self.cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
                self.conn.commit()
                self.students.append(name)
                self.add_student_row(name)
            except sqlite3.IntegrityError:
                pass
            self.name_input.text = ''

    def load_attendance(self):
        for name in self.students:
            self.add_student_row(name)

    def add_student_row(self, name):
        status = self.get_attendance_status(name, self.today)

        layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        label = Label(text=name, size_hint_x=0.6)

        present_btn = Button(text='Present', size_hint_x=0.2)
        absent_btn = Button(text='Absent', size_hint_x=0.2)

        if status == 'Present':
            present_btn.background_color = (0, 0.8, 0, 1)
        elif status == 'Absent':
            absent_btn.background_color = (0.8, 0, 0, 1)

        present_btn.bind(on_press=lambda x, n=name: self.mark_attendance(n, 'Present'))
        absent_btn.bind(on_press=lambda x, n=name: self.mark_attendance(n, 'Absent'))

        layout.add_widget(label)
        layout.add_widget(present_btn)
        layout.add_widget(absent_btn)

        self.attendance_layout.add_widget(layout)

    def get_attendance_status(self, name, date):
        self.cursor.execute("SELECT status FROM attendance_records WHERE name = ? AND date = ?", (name, date))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def mark_attendance(self, name, status):
        self.cursor.execute('''
            INSERT INTO attendance_records (name, date, status)
            VALUES (?, ?, ?)
            ON CONFLICT(name, date) DO UPDATE SET status=excluded.status
        ''', (name, self.today, status))
        self.conn.commit()

        # Refresh UI
        self.attendance_layout.clear_widgets()
        self.load_attendance()

    def on_stop(self):
        self.conn.close()

if __name__ == '__main__':
    AttendanceApp().run()