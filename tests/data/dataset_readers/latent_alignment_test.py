# pylint: disable=invalid-name,no-self-use

from allennlp.common.testing import AllenNlpTestCase
from allennlp.common import Params
from weak_supervision.data.dataset_readers.semantic_parsing.latent_alignment import LatentAlignmentDatasetReader

class TestLatentAlignmentDatasetReader(AllenNlpTestCase):
    def test_reader_can_read(self):
        params = {
                'lazy': False,
                'max_logical_forms': 200,
                }
        reader = LatentAlignmentDatasetReader.from_params(Params(params))
        dataset = reader.read("fixtures/data/wikitables/alignment_preprocessed.json")
        assert len(dataset) == 2

        assert [t.text for t in dataset[0].fields["utterance"].tokens][:3] == ["what", "was", "the"]
        assert len(dataset[0].fields['logical_forms'].field_list) == 201
        lf_tokens = [t.text for t in dataset[0].fields['logical_forms'].field_list[0].tokens]
        assert lf_tokens == ['max', 'reverse', 'fb:cell.cell.date', 'reverse', 'fb:row.row.year',
                             'fb:row.row.league', 'fb:cell.usl_a_league']

        assert [t.text for t in dataset[1].fields["utterance"].tokens][:3] == ["in", "what", "city"]
        assert len(dataset[1].fields['logical_forms'].field_list) == 71
        lf_tokens = [t.text for t in dataset[1].fields['logical_forms'].field_list[0].tokens]
        assert lf_tokens == ['reverse', 'fb:row.row.venue', 'argmax', 'number', '1', 'number', '1',
                             'fb:row.row.position', 'fb:cell.1st', 'reverse', 'lambda', 'x',
                             'reverse', 'fb:row.row.index', 'var', 'x']
