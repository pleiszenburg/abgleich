use colored::Colorize;

pub fn colorized_storage_si_suffix(value: u64) -> String {
    let mut count: u8 = 0;
    #[allow(clippy::cast_precision_loss)]
    let mut state: f64 = value as f64;
    while state >= 1024. && count < 5 {
        state /= 1024.;
        count += 1;
    }
    let number = format!("{state:.02}");
    if count == 0 {
        return format!("{number}   B").bright_cyan().to_string();
    }
    if count == 1 {
        return format!("{number} KiB").bright_green().to_string();
    }
    if count == 2 {
        return format!("{number} MiB").bright_yellow().to_string();
    }
    if count == 3 {
        return format!("{number} GiB").bright_red().to_string();
    }
    if count == 4 {
        return format!("{number} TiB").bright_magenta().to_string();
    }
    format!("{number} PiB").bright_white().to_string()
}

pub fn storage_si_suffix(value: u64) -> String {
    let mut count: u8 = 0;
    #[allow(clippy::cast_precision_loss)]
    let mut state: f64 = value as f64;
    while state >= 1024. && count < 5 {
        state /= 1024.;
        count += 1;
    }
    let number = format!("{state:.02}");
    if count == 0 {
        return format!("{number}   B");
    }
    if count == 1 {
        return format!("{number} KiB");
    }
    if count == 2 {
        return format!("{number} MiB");
    }
    if count == 3 {
        return format!("{number} GiB");
    }
    if count == 4 {
        return format!("{number} TiB");
    }
    format!("{number} PiB")
}

pub fn storage_suffix(value: u64) -> String {
    format!("{value} B")
}
