from pathlib import Path
import tempfile
import unittest
import bridge_client


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'bridge space'
        self.root.mkdir()
        (self.root / 'GPT_Max_Bridge.ms').touch()
        self.source = self.root / 'sample.ms'
        self.source.write_text('format "sample"', encoding='utf-8')

    def test_complete_request_and_unique_receipt(self):
        receipt = bridge_client.submit(self.root, self.source)
        request = (self.root / 'bridge_request.ms').read_text(encoding='utf-8-sig')
        self.assertIn(bridge_client.max_string(receipt), request)
        self.assertIn('throw problem', request)
        self.assertEqual(receipt.with_suffix('.ms').read_bytes(), self.source.read_bytes())
        receipt.write_text('OK\n', encoding='utf-8')
        self.assertEqual(bridge_client.wait_result(receipt, 1), 'OK')

    def test_pending_request_is_never_overwritten(self):
        request = self.root / 'bridge_request.ms'
        request.write_text('existing')
        with self.assertRaises(FileExistsError):
            bridge_client.submit(self.root, self.source)
        self.assertEqual(request.read_text(), 'existing')
        self.assertEqual(list((self.root / 'runtime').iterdir()), [])
        self.assertEqual(list(self.root.glob('.request-*')), [])

    def test_receipt_error_and_timeout(self):
        receipt = self.root / 'result.txt'
        receipt.write_text('ERROR\nexample failure\n')
        self.assertTrue(bridge_client.wait_result(receipt, 1).startswith('ERROR'))
        receipt.unlink()
        with self.assertRaises(TimeoutError):
            bridge_client.wait_result(receipt, 0.01)


if __name__ == '__main__':
    unittest.main()
