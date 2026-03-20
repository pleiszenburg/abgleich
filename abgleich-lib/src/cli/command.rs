use clap::{Parser, Subcommand};

#[derive(Debug, Parser)] // requires `derive` feature
#[command(name = "abgleich")]
#[command(version, about = "abgleich, zfs sync tool", long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

/// Parse a human-readable byte-rate string into bytes per second.
///
/// Accepts a plain integer or an integer followed by one of the suffixes
/// `k`/`K` (× 1 024), `m`/`M` (× 1 024²), or `g`/`G` (× 1 024³).
/// Examples: `"1048576"`, `"1m"`, `"500k"`, `"2g"`.
pub fn parse_rate_limit(s: &str) -> Result<u64, String> {
    if s.is_empty() {
        return Err("rate limit cannot be empty".to_string());
    }
    let split_at = s.find(|c: char| !c.is_ascii_digit()).unwrap_or(s.len());
    let (digits, suffix) = s.split_at(split_at);
    if digits.is_empty() {
        return Err(format!("no numeric value in '{s}'"));
    }
    let base: u64 = digits
        .parse()
        .map_err(|_| format!("invalid number '{digits}'"))?;
    let mult: u64 = match suffix.to_lowercase().as_str() {
        "" => 1,
        "k" => 1_024,
        "m" => 1_024 * 1_024,
        "g" => 1_024 * 1_024 * 1_024,
        other => return Err(format!("unknown suffix '{other}'; use k, m, or g")),
    };
    base.checked_mul(mult)
        .ok_or_else(|| "rate limit value overflows u64".to_string())
}

/// Parse a `host:port` string into `(String, u16)`.
///
/// The host part may be any hostname or IP address.  The port must be a valid
/// `u16`.  The split is on the *last* colon so that IPv6 addresses of the form
/// `::1:18432` are handled correctly (though bare IPv6 should be bracketed).
pub fn parse_insecure(s: &str) -> Result<(String, u16), String> {
    let colon = s
        .rfind(':')
        .ok_or_else(|| format!("expected host:port, got '{s}'"))?;
    let host = &s[..colon];
    let port_str = &s[colon + 1..];
    if host.is_empty() {
        return Err(format!("host part is empty in '{s}'"));
    }
    let port: u16 = port_str
        .parse()
        .map_err(|_| format!("invalid port '{port_str}' in '{s}'"))?;
    Ok((host.to_string(), port))
}

/// Parse an xz compression level string into a `u8`.
///
/// Accepts a single digit `0`–`9`.  Any other input is rejected.
pub fn parse_compress_level(s: &str) -> Result<u8, String> {
    let level: u8 = s
        .parse()
        .map_err(|_| format!("compression level must be 0-9, got '{s}'"))?;
    if level > 9 {
        return Err(format!("compression level must be 0-9, got {level}"));
    }
    Ok(level)
}

#[allow(clippy::doc_markdown)]
#[derive(Debug, Subcommand)]
pub enum Commands {
    /// remove old snapshots from source datasets, freeing up space, while snapshots remain on target
    #[command(arg_required_else_help = true)]
    Free {
        /// output as json
        #[arg(short, long, required = false)]
        json: bool,

        /// answer all questions with yes
        #[arg(short, long, required = false)]
        yes: bool,

        /// attempt all transactions even if some fail; exit non-zero if any failed
        #[arg(short, long, required = false)]
        force: bool,

        /// alias or [route:][user%]root
        #[arg(required = true)]
        source: String,

        /// alias or [route:][user%]root
        #[arg(required = true)]
        target: String,
    },

    /// show list of apools/zpools and/or a list/tree of datasets
    #[command(arg_required_else_help = false)]
    Ls {
        /// output as json
        #[arg(short, long, required = false)]
        json: bool,

        /// void, alias or [route:][user%]root
        location: Option<String>,
    },

    /// create snapshots of changed datasets for backups
    #[command(arg_required_else_help = true)]
    Snap {
        /// output as json
        #[arg(short, long, required = false)]
        json: bool,

        /// answer all questions with yes
        #[arg(short, long, required = false)]
        yes: bool,

        /// attempt all transactions even if some fail; exit non-zero if any failed
        #[arg(short, long, required = false)]
        force: bool,

        /// alias or [route:][user%]root
        #[arg(required = true)]
        location: String,
    },

    /// sync a dataset tree into another
    #[command(arg_required_else_help = true)]
    Sync {
        /// output as json
        #[arg(short = 'j', long, required = false)]
        json: bool,

        /// answer all questions with yes
        #[arg(short = 'y', long, required = false)]
        yes: bool,

        /// run transfer pipe on common entry host, where bash is required
        #[arg(short = 'd', long, required = false)]
        direct: bool,

        /// attempt all transactions even if some fail; exit non-zero if any failed
        #[arg(short = 'f', long, required = false)]
        force: bool,

        /// limit transfer bandwidth on the sending host via pv (e.g. 10m, 500k, 1g)
        #[arg(short = 'r', long, required = false, value_parser = parse_rate_limit)]
        rate_limit: Option<u64>,

        /// xz compression level (0–9); suppresses `zfs send -c` because sending
        /// pre-compressed blocks would reduce xz efficiency.  Omit the flag
        /// entirely to disable xz (uses `zfs send -c` instead).  Pass `-x`
        /// without a value for the default level 5.  Pass `-x N` or `-x=N`
        /// for a specific level (0 = fastest, 9 = best compression).
        #[arg(short = 'x', long, num_args = 0..=1, default_missing_value = "5",
              value_parser = parse_compress_level)]
        compress: Option<u8>,

        /// bypass SSH for data transfer: receiver uses `nc -l PORT | zfs receive`,
        /// sender uses `zfs send | nc HOST PORT`; format: host:port
        /// (mutually exclusive with --direct)
        #[arg(long, required = false, value_parser = parse_insecure)]
        insecure: Option<(String, u16)>,

        /// alias or [route:][user%]root
        #[arg(required = true)]
        source: String,

        /// alias or [route:][user%]root
        #[arg(required = true)]
        target: String,
    },

    /// show version
    Version {},
}

#[cfg(test)]
mod tests {
    use super::{parse_compress_level, parse_insecure, parse_rate_limit};

    #[test]
    fn plain_number() {
        assert_eq!(parse_rate_limit("1048576"), Ok(1_048_576));
    }

    #[test]
    fn suffix_k() {
        assert_eq!(parse_rate_limit("512k"), Ok(512 * 1_024));
    }

    #[test]
    fn suffix_m_uppercase() {
        assert_eq!(parse_rate_limit("10M"), Ok(10 * 1_024 * 1_024));
    }

    #[test]
    fn suffix_g() {
        assert_eq!(parse_rate_limit("2g"), Ok(2 * 1_024 * 1_024 * 1_024));
    }

    #[test]
    fn empty_string_errors() {
        assert!(parse_rate_limit("").is_err());
    }

    #[test]
    fn unknown_suffix_errors() {
        assert!(parse_rate_limit("10t").is_err());
    }

    #[test]
    fn no_digits_errors() {
        assert!(parse_rate_limit("m").is_err());
    }

    // ── parse_compress_level ──────────────────────────────────────────────

    #[test]
    fn compress_level_zero() {
        assert_eq!(parse_compress_level("0"), Ok(0));
    }

    #[test]
    fn compress_level_five() {
        assert_eq!(parse_compress_level("5"), Ok(5));
    }

    #[test]
    fn compress_level_nine() {
        assert_eq!(parse_compress_level("9"), Ok(9));
    }

    #[test]
    fn compress_level_ten_errors() {
        assert!(parse_compress_level("10").is_err());
    }

    #[test]
    fn compress_level_non_numeric_errors() {
        assert!(parse_compress_level("fast").is_err());
    }

    #[test]
    fn compress_level_empty_errors() {
        assert!(parse_compress_level("").is_err());
    }

    // ── parse_insecure ────────────────────────────────────────────────────

    #[test]
    fn insecure_hostname_port() {
        assert_eq!(
            parse_insecure("linux-b:18432"),
            Ok(("linux-b".to_string(), 18432))
        );
    }

    #[test]
    fn insecure_ip_port() {
        assert_eq!(
            parse_insecure("192.168.56.21:18432"),
            Ok(("192.168.56.21".to_string(), 18432))
        );
    }

    #[test]
    fn insecure_ipv6_last_colon_used_for_split() {
        // Bare IPv6: last colon separates port.
        let result = parse_insecure("::1:18432");
        assert_eq!(result, Ok(("::1".to_string(), 18432)));
    }

    #[test]
    fn insecure_no_colon_errors() {
        assert!(parse_insecure("linux-b").is_err());
    }

    #[test]
    fn insecure_empty_host_errors() {
        assert!(parse_insecure(":18432").is_err());
    }

    #[test]
    fn insecure_invalid_port_errors() {
        assert!(parse_insecure("linux-b:notaport").is_err());
    }

    #[test]
    fn insecure_port_overflow_errors() {
        assert!(parse_insecure("linux-b:99999").is_err());
    }
}
