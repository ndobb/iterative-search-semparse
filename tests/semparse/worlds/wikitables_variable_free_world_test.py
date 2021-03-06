# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-many-public-methods
from typing import List
from functools import partial

from allennlp.common.testing import AllenNlpTestCase
from allennlp.data.tokenizers import Token
from allennlp.semparse import ParsingError

from weak_supervision.semparse.contexts import TableQuestionContext
from weak_supervision.semparse.type_declarations import wikitables_variable_free as types
from weak_supervision.semparse.worlds import WikiTablesVariableFreeWorld


def check_productions_match(actual_rules: List[str], expected_right_sides: List[str]):
    actual_right_sides = [rule.split(' -> ')[1] for rule in actual_rules]
    assert set(actual_right_sides) == set(expected_right_sides)


class TestWikiTablesVariableFreeWorld(AllenNlpTestCase):
    def setUp(self):
        super().setUp()
        question_tokens = [Token(x) for x in ['what', 'was', 'the', 'last', 'year', '2013', '?']]
        self.table_file = self.FIXTURES_ROOT / 'data' / 'wikitables' / 'sample_table.tagged'
        self.table_context = TableQuestionContext.read_from_file(self.table_file, question_tokens)
        self.world_with_2013 = WikiTablesVariableFreeWorld(self.table_context)
        usl_league_tokens = [Token(x) for x in ['what', 'was', 'the', 'last', 'year', 'with', 'usl',
                                                'a', 'league', '?']]
        self.world_with_usl_a_league = self._get_world_with_question_tokens(usl_league_tokens)

    def _get_world_with_question_tokens(self, tokens: List[Token]) -> WikiTablesVariableFreeWorld:
        table_context = TableQuestionContext.read_from_file(self.table_file, tokens)
        world = WikiTablesVariableFreeWorld(table_context)
        return world

    def test_get_valid_actions_returns_correct_set(self):
        # This test is long, but worth it.  These are all of the valid actions in the grammar, and
        # we want to be sure they are what we expect.
        valid_actions = self.world_with_2013.get_valid_actions()
        assert set(valid_actions.keys()) == {
                "<r,<t,s>>",
                "<r,<m,d>>",
                "<r,<f,<n,r>>>",
                "<r,<c,r>>",
                "<r,<g,r>>",
                "<r,<r,<f,n>>>",
                "<r,<t,<s,r>>>",
                "<n,<n,<n,d>>>",
                "<r,<m,<d,r>>>",
                "<r,<f,n>>",
                "<r,r>",
                "<r,n>",
                "d",
                "n",
                "s",
                "m",
                "t",
                "f",
                "r",
                "@start@",
                }

        check_productions_match(valid_actions['<r,<t,s>>'],
                                ['mode_string', 'select_string'])

        check_productions_match(valid_actions['<r,<m,d>>'],
                                ['mode_date', 'select_date',
                                 'max_date', 'min_date'])

        check_productions_match(valid_actions['<r,<f,n>>'],
                                ['mode_number', 'select_number',
                                 'average', 'max_number', 'min_number',
                                 'sum'])

        check_productions_match(valid_actions['<r,<f,<n,r>>>'],
                                ['filter_number_equals', 'filter_number_greater',
                                 'filter_number_greater_equals', 'filter_number_lesser',
                                 'filter_number_lesser_equals', 'filter_number_not_equals'])

        check_productions_match(valid_actions['<r,<c,r>>'],
                                ['argmax', 'argmin'])

        check_productions_match(valid_actions['<r,<g,r>>'],
                                ['same_as'])

        check_productions_match(valid_actions['<r,<r,<f,n>>>'],
                                ['diff'])

        check_productions_match(valid_actions['<r,<t,<s,r>>>'],
                                ['filter_in', 'filter_not_in'])

        check_productions_match(valid_actions['<n,<n,<n,d>>>'],
                                ['date'])

        check_productions_match(valid_actions['<r,<m,<d,r>>>'],
                                ['filter_date_equals', 'filter_date_greater',
                                 'filter_date_greater_equals', 'filter_date_lesser',
                                 'filter_date_lesser_equals', 'filter_date_not_equals'])

        check_productions_match(valid_actions['<r,r>'],
                                ['first', 'last', 'next', 'previous'])

        check_productions_match(valid_actions['<r,n>'],
                                ['count'])

        # These are the columns in table, and are instance specific.
        check_productions_match(valid_actions['m'],
                                ['date_column:year'])

        check_productions_match(valid_actions['f'],
                                ['number_column:avg_attendance',
                                 'number_column:division',
                                 'number_column:year',
                                 'number_column:open_cup',
                                 'number_column:regular_season'])

        check_productions_match(valid_actions['t'],
                                ['string_column:league',
                                 'string_column:playoffs',
                                 'string_column:open_cup',
                                 'string_column:regular_season',
                                 'string_column:year',
                                 'string_column:division',
                                 'string_column:avg_attendance'])

        check_productions_match(valid_actions['@start@'],
                                ['d', 'n', 's'])

        # The question does not produce any strings. It produces just a number.
        check_productions_match(valid_actions['s'],
                                ['[<r,<t,s>>, r, t]'])

        check_productions_match(valid_actions['d'],
                                ['[<n,<n,<n,d>>>, n, n, n]',
                                 '[<r,<m,d>>, r, m]'])

        check_productions_match(valid_actions['n'],
                                ['2013',
                                 '-1',
                                 '[<r,<f,n>>, r, f]',
                                 '[<r,<r,<f,n>>>, r, r, f]',
                                 '[<r,n>, r]'])

        check_productions_match(valid_actions['r'],
                                ['all_rows',
                                 '[<r,<m,<d,r>>>, r, m, d]',
                                 '[<r,<g,r>>, r, m]',
                                 '[<r,<g,r>>, r, f]',
                                 '[<r,<g,r>>, r, t]',
                                 '[<r,<c,r>>, r, m]',
                                 '[<r,<c,r>>, r, f]',
                                 '[<r,<f,<n,r>>>, r, f, n]',
                                 '[<r,<t,<s,r>>>, r, t, s]',
                                 '[<r,r>, r]'])

    def test_parsing_logical_form_with_string_not_in_question_fails(self):
        logical_form_with_usl_a_league = """(select (filter_in all_rows string_column:league usl_a_league)
                                             date_column:year)"""
        logical_form_with_2013 = """(select (filter_date_greater all_rows date_column:year (date 2013 -1 -1))
                                     date_column:year)"""
        with self.assertRaises(ParsingError):
            self.world_with_2013.parse_logical_form(logical_form_with_usl_a_league)
            self.world_with_usl_a_league.parse_logical_form(logical_form_with_2013)

    @staticmethod
    def _get_alias(types_, name) -> str:
        if name in types_.generic_name_mapper.common_name_mapping:
            return types_.generic_name_mapper.get_alias(name)
        elif name in types_.string_column_name_mapper.common_name_mapping:
            return types_.string_column_name_mapper.get_alias(name)
        elif name in types_.number_column_name_mapper.common_name_mapping:
            return types_.number_column_name_mapper.get_alias(name)
        elif name in types_.date_column_name_mapper.common_name_mapping:
            return types_.date_column_name_mapper.get_alias(name)
        else:
            return types_.comparable_column_name_mapper.get_alias(name)

    def test_world_processes_logical_forms_correctly(self):
        logical_form = """(select_date (filter_in all_rows string_column:league string:usl_a_league)
                            date_column:year)"""
        expression = self.world_with_usl_a_league.parse_logical_form(logical_form)
        f = partial(self._get_alias, types)
        # Cells (and parts) get mapped to strings.
        # Column names are mapped in local name mapping. For the global names, we can get their
        # aliases from the name mapper.
        mapping = self.world_with_2013.local_name_mapping
        year_alias = mapping['date_column:year']
        league_alias = mapping['string_column:league']
        # pylint: disable=line-too-long
        assert str(expression) == \
        f"{f('select_date')}({f('filter_in')}({f('all_rows')},{league_alias},string:usl_a_league),{year_alias})"

    def test_world_gets_correct_actions(self):
        logical_form = """(select_date (filter_in all_rows string_column:league string:usl_a_league)
                            date_column:year)"""
        expression = self.world_with_usl_a_league.parse_logical_form(logical_form)
        expected_sequence = ['@start@ -> d', 'd -> [<r,<m,d>>, r, m]', '<r,<m,d>> -> select_date',
                             'r -> [<r,<t,<s,r>>>, r, t, s]', '<r,<t,<s,r>>> -> filter_in',
                             'r -> all_rows', 't -> string_column:league', 's -> string:usl_a_league',
                             'm -> date_column:year']
        assert self.world_with_usl_a_league.get_action_sequence(expression) == expected_sequence

    def test_world_gets_logical_form_from_actions(self):
        # pylint: disable=line-too-long
        logical_form = """(select_date (filter_in all_rows string_column:league string:usl_a_league) date_column:year)"""
        expression = self.world_with_usl_a_league.parse_logical_form(logical_form)
        action_sequence = self.world_with_usl_a_league.get_action_sequence(expression)
        reconstructed_logical_form = self.world_with_usl_a_league.get_logical_form(action_sequence)
        assert logical_form == reconstructed_logical_form

    def test_world_processes_logical_forms_with_number_correctly(self):
        tokens = [Token(x) for x in ['when', 'was', 'the', 'attendance', 'higher', 'than', '3000',
                                     '?']]
        world = self._get_world_with_question_tokens(tokens)
        logical_form = """(select_date (filter_number_greater all_rows number_column:avg_attendance 3000)
                           date_column:year)"""
        expression = world.parse_logical_form(logical_form)
        f = partial(self._get_alias, types)
        # Cells (and parts) get mapped to strings.
        # Column names are mapped in local name mapping. For the global names, we can get their
        # aliases from the name mapper.
        mapping = world.local_name_mapping
        avg_attendance_alias = mapping['number_column:avg_attendance']
        year_alias = mapping['date_column:year']
        # pylint: disable=line-too-long
        assert str(expression) == \
        f"{f('select_date')}({f('filter_number_greater')}({f('all_rows')},{avg_attendance_alias},num:3000),{year_alias})"

    def test_world_processes_logical_forms_with_date_correctly(self):
        logical_form = """(select_date (filter_date_greater all_rows date_column:year (date 2013 -1 -1))
                           date_column:year)"""
        expression = self.world_with_2013.parse_logical_form(logical_form)
        f = partial(self._get_alias, types)
        # Cells (and parts) get mapped to strings.
        # Column names are mapped in local name mapping. For the global names, we can get their
        # aliases from the name mapper.
        mapping = self.world_with_2013.local_name_mapping
        year_alias = mapping['date_column:year']
        # pylint: disable=line-too-long
        assert str(expression) == \
        f"{f('select_date')}({f('filter_date_greater')}({f('all_rows')},{year_alias},{f('date')}(num:2013,num:~1,num:~1)),{year_alias})"

    def test_get_agenda(self):
        tokens = [Token(x) for x in ['what', 'was', 'the', 'difference', 'in', 'attendance',
                                     'between', 'years', '2001', 'and', '2005', '?']]
        world = self._get_world_with_question_tokens(tokens)
        # "year" column does not match because "years" occurs in the question.
        assert set(world.get_agenda()) == {'n -> 2001',
                                           'n -> 2005',
                                           's -> string:2005',
                                           's -> string:2001',
                                           '<r,<m,<d,r>>> -> filter_date_equals',
                                           '<r,<r,<f,n>>> -> diff'}
        # Conservative agenda does not have strings and numbers because they have multiple types.
        assert set(world.get_agenda(conservative=True)) == {'<r,<r,<f,n>>> -> diff',
                                                            '<r,<m,<d,r>>> -> filter_date_equals'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'total', 'avg.', 'attendance', 'in',
                                     'years', '2001', 'and', '2005', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'n -> 2001',
                                           'n -> 2005',
                                           's -> string:2005',
                                           's -> string:2001',
                                           '<r,<f,n>> -> sum',
                                           '<r,<m,<d,r>>> -> filter_date_equals',
                                           't -> string_column:avg_attendance',
                                           'f -> number_column:avg_attendance'}
        # Conservative disallows "sum" for the question word "total" too.
        assert set(world.get_agenda(conservative=True)) == {'<r,<m,<d,r>>> -> filter_date_equals'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'average', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<f,n>> -> average',
                                           't -> string_column:avg_attendance',
                                           'f -> number_column:avg_attendance'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<f,n>> -> average'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'largest', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<c,r>> -> argmax',
                                           't -> string_column:avg_attendance',
                                           'f -> number_column:avg_attendance'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<c,r>> -> argmax'}

        tokens = [Token(x) for x in ['when', 'was', 'the', 'least', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<c,r>> -> argmin', 't -> string_column:avg_attendance',
                                           '<r,<m,d>> -> select_date',
                                           'f -> number_column:avg_attendance'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<c,r>> -> argmin',
                                                            '<r,<m,d>> -> select_date'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'attendance', 'after', 'the',
                                     'time', 'with', 'the', 'least', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<c,r>> -> argmin', 't -> string_column:avg_attendance',
                                           '<r,r> -> next',
                                           'f -> number_column:avg_attendance'}
        # conservative disallows "after" mapping to "next"
        assert set(world.get_agenda(conservative=True)) == {'<r,<c,r>> -> argmin'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'attendance', 'below', 'the',
                                     'row', 'with', 'the', 'least', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<c,r>> -> argmin', 't -> string_column:avg_attendance',
                                           '<r,r> -> next',
                                           'f -> number_column:avg_attendance'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<c,r>> -> argmin',
                                                            '<r,r> -> next'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'attendance', 'before', 'the',
                                     'time', 'with', 'the', 'least', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<c,r>> -> argmin', 't -> string_column:avg_attendance',
                                           '<r,r> -> previous',
                                           'f -> number_column:avg_attendance'}
        # conservative disallows "before" mapping to "previous"
        assert set(world.get_agenda(conservative=True)) == {'<r,<c,r>> -> argmin'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'attendance', 'above', 'the',
                                     'row', 'with', 'the', 'least', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<c,r>> -> argmin', 't -> string_column:avg_attendance',
                                           '<r,r> -> previous',
                                           'f -> number_column:avg_attendance'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<c,r>> -> argmin',
                                                            '<r,r> -> previous'}

        tokens = [Token(x) for x in ['when', 'was', 'the', 'avg.', 'attendance', 'same', 'as', 'when',
                                     'the', 'league', 'was', 'usl', 'a', 'league', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'t -> string_column:avg_attendance',
                                           'f -> number_column:avg_attendance',
                                           't -> string_column:league',
                                           's -> string:usl_a_league',
                                           '<r,<g,r>> -> same_as',
                                           '<r,<m,d>> -> select_date'}
        assert set(world.get_agenda(conservative=True)) == {'t -> string_column:league',
                                                            's -> string:usl_a_league',
                                                            '<r,<g,r>> -> same_as',
                                                            '<r,<m,d>> -> select_date'}

        tokens = [Token(x) for x in ['what', 'is', 'the', 'least', 'avg.', 'attendance', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<f,n>> -> min_number', 't -> string_column:avg_attendance',
                                           'f -> number_column:avg_attendance'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<f,n>> -> min_number'}

        tokens = [Token(x) for x in ['when', 'did', 'the', 'team', 'not', 'qualify', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<m,d>> -> select_date', 's -> string:qualify'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<m,d>> -> select_date', 's -> string:qualify'}

        tokens = [Token(x) for x in ['when', 'was', 'the', 'avg.', 'attendance', 'at', 'least',
                                     '7000', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<f,<n,r>>> -> filter_number_greater_equals',
                                           '<r,<m,d>> -> select_date',
                                           'f -> number_column:avg_attendance',
                                           't -> string_column:avg_attendance', 'n -> 7000'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<f,<n,r>>> -> filter_number_greater_equals',
                                                            '<r,<m,d>> -> select_date',
                                                            'n -> 7000'}

        tokens = [Token(x) for x in ['when', 'was', 'the', 'avg.', 'attendance', 'more', 'than',
                                     '7000', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<f,<n,r>>> -> filter_number_greater',
                                           '<r,<m,d>> -> select_date',
                                           'f -> number_column:avg_attendance',
                                           't -> string_column:avg_attendance', 'n -> 7000'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<f,<n,r>>> -> filter_number_greater',
                                                            '<r,<m,d>> -> select_date',
                                                            'n -> 7000'}

        tokens = [Token(x) for x in ['when', 'was', 'the', 'avg.', 'attendance', 'at', 'most',
                                     '7000', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<f,<n,r>>> -> filter_number_lesser_equals',
                                           '<r,<m,d>> -> select_date',
                                           'f -> number_column:avg_attendance',
                                           't -> string_column:avg_attendance', 'n -> 7000'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<f,<n,r>>> -> filter_number_lesser_equals',
                                                            '<r,<m,d>> -> select_date',
                                                            'n -> 7000'}

        tokens = [Token(x) for x in ['when', 'was', 'the', 'avg.', 'attendance', 'no', 'more',
                                     'than', '7000', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,<f,<n,r>>> -> filter_number_lesser_equals',
                                           '<r,<m,d>> -> select_date',
                                           'f -> number_column:avg_attendance',
                                           't -> string_column:avg_attendance', 'n -> 7000'}
        assert set(world.get_agenda(conservative=True)) == {'<r,<f,<n,r>>> -> filter_number_lesser_equals',
                                                            '<r,<m,d>> -> select_date',
                                                            'n -> 7000'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'top', 'year', '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,r> -> first', 't -> string_column:year',
                                           'f -> number_column:year',
                                           'm -> date_column:year'}
        assert set(world.get_agenda(conservative=True)) == {'<r,r> -> first'}

        tokens = [Token(x) for x in ['what', 'was', 'the', 'year', 'in', 'the', 'bottom', 'row',
                                     '?']]
        world = self._get_world_with_question_tokens(tokens)
        assert set(world.get_agenda()) == {'<r,r> -> last', 't -> string_column:year',
                                           'f -> number_column:year',
                                           'm -> date_column:year'}
        assert set(world.get_agenda(conservative=True)) == {'<r,r> -> last'}
