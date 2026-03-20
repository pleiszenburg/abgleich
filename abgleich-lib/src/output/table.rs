use console::measure_text_width;

#[derive(PartialEq, Eq)]
pub enum Alignment {
    Left,
    Right,
}

pub struct TableColumn {
    name: String,
    alignment: Alignment,
    fields: Vec<String>,
    width: usize,
}

impl TableColumn {
    pub fn new(name: String, alignment: Alignment) -> Self {
        Self {
            width: measure_text_width(&name),
            name,
            alignment,
            fields: Vec::new(),
        }
    }

    pub const fn rows(&self) -> usize {
        self.fields.len()
    }

    pub fn push_field(&mut self, field: String) {
        let field_len = measure_text_width(&field);
        if field_len > self.width {
            self.width = field_len;
        }
        self.fields.push(field);
    }

    pub fn print_field(&self, row: usize) {
        self.print_item(&self.fields[row]);
    }

    pub fn print_head(&self) {
        self.print_item(&self.name);
    }

    fn print_item(&self, value: &str) {
        let diff = self.width - measure_text_width(value);
        let fill = str::repeat(" ", diff);
        match self.alignment {
            Alignment::Left => {
                print!("| {value}{fill} ");
            }
            Alignment::Right => {
                print!("| {fill}{value} ");
            }
        }
    }

    pub fn print_bar(&self) {
        let buff = str::repeat("-", self.width);
        print!("|-{buff}-");
    }

    pub fn print_end() {
        println!("|");
    }
}

pub struct Table {
    columns: Vec<TableColumn>,
}

impl Table {
    pub const fn new(columns: Vec<TableColumn>) -> Self {
        Self { columns }
    }

    pub fn rows(&self) -> usize {
        self.columns
            .iter()
            .map(TableColumn::rows)
            .min()
            .unwrap_or(0)
    }

    pub fn push_row(&mut self, mut columns: Vec<String>) {
        while columns.len() < self.columns.len() {
            columns.push(String::new()); // padding
        }
        for (field, column) in columns.into_iter().zip(self.columns.iter_mut()) {
            column.push_field(field);
        }
    }

    pub fn print(&self) {
        self.print_head();
        self.print_bar();
        for row in 0..self.rows() {
            self.print_row(row);
        }
    }

    fn print_bar(&self) {
        for column in &self.columns {
            column.print_bar();
        }
        TableColumn::print_end();
    }

    fn print_head(&self) {
        for column in &self.columns {
            column.print_head();
        }
        TableColumn::print_end();
    }

    fn print_row(&self, row: usize) {
        for column in &self.columns {
            column.print_field(row);
        }
        TableColumn::print_end();
    }
}
