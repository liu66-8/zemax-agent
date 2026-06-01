#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Child, Stdio};
use std::io::{BufRead, BufReader};
use std::sync::Mutex;
use tauri::State;

struct PythonProcess(Mutex<Option<Child>>);

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let python = Command::new("python")
                .args(["-m", "zemax_agent.main"])
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn();

            match python {
                Ok(mut child) => {
                    let stdout = child.stdout.take();
                    if let Some(stdout) = stdout {
                        let reader = BufReader::new(stdout);
                        std::thread::spawn(move || {
                            for line in reader.lines() {
                                if let Ok(l) = line {
                                    println!("[Python] {}", l);
                                }
                            }
                        });
                    }
                    app.manage(PythonProcess(Mutex::new(Some(child))));
                    println!("Python backend started");
                }
                Err(e) => {
                    eprintln!("Failed to start Python backend: {}", e);
                    app.manage(PythonProcess(Mutex::new(None)));
                }
            }
            Ok(())
        })
        .on_window_event(|_window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                std::process::exit(0);
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Zemax Agent");
}
