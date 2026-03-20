/// Options that modify how `zfs send | zfs receive` pipelines are built.
#[derive(Clone, Debug, Default)]
pub struct TransferOptions {
    /// Optional bandwidth cap applied on the sending host via `pv -q -L N`.
    /// Value is bytes per second.
    pub rate_limit: Option<u64>,
    /// When `Some(level)`, pipe through `xz -N` (level 0–9) on the sending
    /// host and `xz -d` on the receiving host.  Also suppresses `zfs send -c`
    /// because pre-compressed blocks reduce xz efficiency.  `None` means no
    /// xz compression; `zfs send -c` is then used instead.
    pub compress: Option<u8>,
    /// When `Some((host, port))`, bypass SSH for the data stream: the
    /// receiver listens with `nc -l PORT | … | zfs receive` and the sender
    /// pipes into `nc HOST PORT`.  SSH is still used to start both sides.
    /// Mutually exclusive with the `direct` flag.
    pub insecure: Option<(String, u16)>,
}
