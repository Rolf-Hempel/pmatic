import os
import time

class Protocol:
    def __init__(self, log_file, archive_file, max_records, print_to_stdout= False):
        """Remember the file names and maximal line count."""
        self.log_file = log_file
        self.archive_file = archive_file
        self.max_records = max_records
        self.print_to_stdout = print_to_stdout
        self.record_count = 0

        # If the protocol file does not exist, create it.
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass

    def protocol_out(self, record):
        """Add a new protocol line to protocol file. If the maximal line count is reached, archive the file."""
        with open(self.log_file, 'a') as f:
            f.write(record + '\n')

        if self.print_to_stdout:
            print(record)

        self.record_count += 1

        if self.record_count >= self.max_records:
            self.archive_log()
            self.reset_log()

    def archive_log(self):
        """Replaces the archive file with the current protocol file."""
        if os.path.exists(self.archive_file):
            # Save the archive file before overwriting, if it exists already.
            if os.path.exists(self.archive_file + ".bak"):
                os.remove(self.archive_file + ".bak")
            os.rename(self.archive_file, self.archive_file + ".bak")
            #shutil.move(self.archive_file, self.archive_file + ".bak")
        os.rename(self.log_file, self.archive_file)
        #shutil.move(self.log_file, self.archive_file)

    def reset_log(self):
        """Start a mew protocol file."""
        self.record_count = 0
        with open(self.log_file, 'w') as f:
            pass


def main():
    log_file = 'logfile.txt'
    archive_file = 'archive.txt'
    max_records = 10

    protocol = Protocol(log_file, archive_file, max_records)

    for i in range(1, 16):
        record = "Record {i}"
        protocol.protocol_out(record)
        print("Protokolliert: {record}")
        time.sleep(0.3)


if __name__ == '__main__':
    main()