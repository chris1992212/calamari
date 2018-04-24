from edit_distance import edit_distance

from calamari_ocr.ocr.text_processing import synchronize
from calamari_ocr.ocr.text_processing import DefaultTextPreprocessor


class Evaluator:
    def __init__(self, text_preprocessor=None):
        self.text_preprocessor = text_preprocessor if text_preprocessor is not None else DefaultTextPreprocessor()

    def run(self, _sentinel=None, gt_dataset=None, pred_dataset=None, progress_bar=False):
        if _sentinel:
            raise Exception("You must call run by using parameter names.")

        gt_dataset.load_samples(progress_bar=progress_bar)
        pred_dataset.load_samples(progress_bar=progress_bar)

        gt_data = self.text_preprocessor.apply(gt_dataset.text_samples(), progress_bar=progress_bar)
        pred_data = self.text_preprocessor.apply(pred_dataset.text_samples(), progress_bar=progress_bar)

        return self.evaluate(gt_data=gt_data, pred_data=pred_data, progress_bar=progress_bar)

    @staticmethod
    def evaluate(_sentinel=None, gt_data=None, pred_data=None, progress_bar=False):
        if len(gt_data) != len(pred_data):
            raise Exception("Mismatch in gt and pred files count: {} vs {}".format(len(gt_data), len(pred_data)))

        total_chars = 0
        total_char_errs = 0
        confusion = {}
        total_sync_errs = 0
        for gt, pred in zip(gt_data, pred_data):
            errs, trues = edit_distance(gt, pred)
            total_chars += len(gt)
            total_char_errs += errs
            synclist = synchronize([gt, pred])
            for sync in synclist:
                gt_str, pred_str = sync.get_text()
                if gt_str != pred_str:
                    key = (gt_str, pred_str)
                    total_sync_errs += max(len(gt_str), len(pred_str))
                    if key not in confusion:
                        confusion[key] = 1
                    else:
                        confusion[key] += 1

        # Note the sync errs can be higher than the true edit distance because
        # replacements are counted as 1
        # e.g. ed(in ewych, ierg ch) = 5
        #      sync(in ewych, ierg ch) = [{i: i}, {n: erg}, {ewy: }, {ch: ch}] = 6

        return {
            "avg_ler": total_char_errs / total_chars,
            "total_chars": total_chars,
            "total_char_errs": total_char_errs,
            "total_sync_errs": total_sync_errs,
            "confusion": confusion,
        }

