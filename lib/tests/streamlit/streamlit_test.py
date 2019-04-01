import json
import os
import re
import textwrap
import time
import unittest

import numpy as np
import pandas as pd
import streamlit as st

from mock import call, patch

from streamlit import __version__
from streamlit import protobuf
from streamlit.Chart import Chart

from google.protobuf import json_format


def get_version():
    """Get version by parsing out setup.py."""
    dirname = os.path.dirname(__file__)
    base_dir = os.path.abspath(os.path.join(dirname, '../..'))
    pattern = re.compile(
        r'(?:.*version=\')(?P<version>.*)(?:\',  # PEP-440$)')
    for line in open(os.path.join(base_dir, 'setup.py')).readlines():
        m = pattern.match(line)
        if m:
            return m.group('version')


def get_last_delta_element(dg):
    return dg._queue.get_deltas()[-1].new_element


class StreamlitTest(unittest.TestCase):
    """Test Streamlit.__init__.py."""

    def test_streamlit_version(self):
        """Test streamlit.__version__."""
        self.assertEqual(__version__, get_version())

    def test_get_option(self):
        """Test streamlit.get_option."""
        # This is set in lib/tests/conftest.py to False
        self.assertEqual(False, st.get_option('browser.gatherUsageStats'))

    def test_set_option(self):
        """Test streamlit.set_option."""
        # This is set in lib/tests/conftest.py to off
        self.assertEqual('off', st.get_option('global.sharingMode'))

        st.set_option('global.sharingMode', 'streamlit-public')
        self.assertEqual(
            'streamlit-public',
            st.get_option('global.sharingMode')
        )


class StreamlitAPITest(unittest.TestCase):
    """Test Public Streamlit Public APIs.

    Unit tests for https://streamlit.io/secret/docs/#api
    """

    def test_st_altair_chart(self):
        """Test st.altair_chart."""
        import altair as alt

        df = pd.DataFrame(np.random.randn(3, 3), columns=['a', 'b', 'c'])

        c = (alt.Chart(df)
            .mark_circle()
            .encode(x='a', y='b', size='c', color='c')
            .interactive())
        dg = st.altair_chart(c)

        el = get_last_delta_element(dg)
        spec = json.loads(el.vega_lite_chart.spec)

        # Checking vega lite is a lot of work so rather than doing that, we
        # just checked to see if the spec data name matches the dataset.
        self.assertEqual(
            spec.get('data').get('name'),
            el.vega_lite_chart.datasets[0].name)

    def test_st_area_chart(self):
        """Test st.area_chart."""
        df = pd.DataFrame([[10, 20, 30]], columns=['a', 'b', 'c'])
        dg = st.area_chart(df, width=640, height=480)

        el = get_last_delta_element(dg)
        self.assertEqual(el.chart.type, 'AreaChart')
        self.assertEqual(el.chart.width, 640)
        self.assertEqual(el.chart.height, 480)
        self.assertEqual(
            el.chart.data.columns.plain_index.data.strings.data,
            ['a', 'b', 'c']
        )
        data = json.loads(json_format.MessageToJson(el.chart.data.data))
        result = [x['int64s']['data'][0] for x in data['cols']]
        self.assertEqual(result, ['10', '20', '30'])

    def test_st_audio(self):
        """Test st.audio."""
        # TODO(armando): generate real audio data
        # For now it doesnt matter cause browser is the one that uses it.
        fake_audio_data = '\x11\x22\x33\x44\x55\x66'.encode('utf-8')

        dg = st.audio(fake_audio_data)

        el = get_last_delta_element(dg)
        # Manually base64 encoded payload above via
        # base64.b64encode(bytes('\x11\x22\x33\x44\x55\x66'.encode('utf-8')))
        self.assertEqual(el.audio.data, 'ESIzRFVm')
        self.assertEqual(el.audio.format, 'audio/wav')

    def test_st_balloons(self):
        """Test st.balloons."""
        with patch('random.randrange') as p:
            p.return_value = 0xDEADBEEF
            dg = st.balloons()

        el = get_last_delta_element(dg)
        self.assertEqual(el.balloons.type, protobuf.Balloons.DEFAULT)
        self.assertEqual(el.balloons.execution_id, 0xDEADBEEF)

    def test_st_bar_chart(self):
        """Test st.bar_chart."""
        df = pd.DataFrame([[10, 20, 30]], columns=['a', 'b', 'c'])
        dg = st.bar_chart(df, width=640, height=480)

        el = get_last_delta_element(dg)
        self.assertEqual(el.chart.type, 'BarChart')
        self.assertEqual(el.chart.width, 640)
        self.assertEqual(el.chart.height, 480)
        self.assertEqual(
            el.chart.data.columns.plain_index.data.strings.data,
            ['a', 'b', 'c']
        )
        data = json.loads(json_format.MessageToJson(el.chart.data.data))
        result = [x['int64s']['data'][0] for x in data['cols']]
        self.assertEqual(result, ['10', '20', '30'])

    def test_st_code(self):
        """Test st.code."""
        dg = st.code('print(\'My string = %d\' % my_value)',
                     language='python')
        expected = textwrap.dedent('''
            ```python
            print('My string = %d' % my_value)
            ```
        ''')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, expected.strip())
        self.assertEqual(el.text.format, protobuf.Text.MARKDOWN)

    def test_st_dataframe(self):
        """Test st.dataframe."""
        pass

    def test_st_deck_gl_chart(self):
        """Test st.deck_gl_chart."""
        df = pd.DataFrame({
            'lat': [1, 2, 3, 4],
            'lon': [11, 22, 33, 44],
        })
        dg = st.deck_gl_chart(df)

        el = get_last_delta_element(dg)
        self.assertEqual(el.deck_gl_chart.HasField('data'), False)
        self.assertEqual(json.loads(el.deck_gl_chart.spec), {})

        data = el.deck_gl_chart.layers[0].data
        self.assertEqual(
            json.loads(json_format.MessageToJson(data.data.cols[0].int64s)),
            {
                'data': ['1', '2', '3', '4']
            }
        )
        self.assertEqual(
            json.loads(json_format.MessageToJson(data.data.cols[1].int64s)),
            {
                'data': ['11', '22', '33', '44']
            }
        )

        self.assertEqual(
            json.loads(json_format.MessageToJson(data.columns.plain_index.data.strings)),
            {
                'data': ['lat', 'lon']
            }
        )

        # Default layer
        self.assertEqual(
            json.loads(el.deck_gl_chart.layers[0].spec),
            {'type': 'ScatterplotLayer'}
        )

    def test_st_empty(self):
        """Test st.empty."""
        dg = st.empty()

        el = get_last_delta_element(dg)
        self.assertEqual(el.empty.unused, True)

    def test_st_error(self):
        """Test st.error."""
        dg = st.error('some error')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, 'some error')
        self.assertEqual(el.text.format, protobuf.Text.ERROR)

    def test_st_exception(self):
        """Test st.exception."""
        pass

    def test_st_header(self):
        """Test st.header."""
        dg = st.header('some header')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, '## some header')
        self.assertEqual(el.text.format, protobuf.Text.MARKDOWN)

    def test_st_help(self):
        """Test st.help."""
        dg = st.help(st.header)

        el = get_last_delta_element(dg)
        self.assertEqual(el.doc_string.name, 'header')
        self.assertEqual(el.doc_string.module, 'streamlit')
        self.assertTrue(
            el.doc_string.doc_string.startswith('Display text in header formatting.'))
        self.assertEqual(el.doc_string.type, '<class \'function\'>')
        self.assertEqual(el.doc_string.signature, '(body)')

    def test_st_image(self):
        """Test st.image."""
        pass

    def test_st_info(self):
        """Test st.info."""
        dg = st.info('some info')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, 'some info')
        self.assertEqual(el.text.format, protobuf.Text.INFO)

    def test_st_json(self):
        """Test st.json."""
        dg = st.json('{"some": "json"}')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, '{"some": "json"}')
        self.assertEqual(el.text.format, protobuf.Text.JSON)

    def test_st_line_chart(self):
        """Test st.line_chart."""
        df = pd.DataFrame([[10, 20, 30]], columns=['a', 'b', 'c'])
        dg = st.line_chart(df, width=640, height=480)

        el = get_last_delta_element(dg)
        self.assertEqual(el.chart.type, 'LineChart')
        self.assertEqual(el.chart.width, 640)
        self.assertEqual(el.chart.height, 480)
        self.assertEqual(
            el.chart.data.columns.plain_index.data.strings.data,
            ['a', 'b', 'c']
        )
        data = json.loads(json_format.MessageToJson(el.chart.data.data))
        result = [x['int64s']['data'][0] for x in data['cols']]
        self.assertEqual(result, ['10', '20', '30'])

    def test_st_map(self):
        """Test st.map."""
        pass

    def test_st_markdown(self):
        """Test st.markdown."""
        dg = st.markdown('    some markdown  ')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, 'some markdown')
        self.assertEqual(el.text.format, protobuf.Text.MARKDOWN)

    def test_st_progress(self):
        """Test st.progress."""
        dg = st.progress(51)

        el = get_last_delta_element(dg)
        self.assertEqual(el.progress.value, 51)

    def test_st_pyplot(self):
        """Test st.pyplot."""
        pass

    def test_st_subheader(self):
        """Test st.subheader."""
        dg = st.subheader('some subheader')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, '### some subheader')
        self.assertEqual(el.text.format, protobuf.Text.MARKDOWN)

    def test_st_success(self):
        """Test st.success."""
        dg = st.success('some success')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, 'some success')
        self.assertEqual(el.text.format, protobuf.Text.SUCCESS)

    def test_st_table(self):
        """Test st.table."""
        pass

    def test_st_text(self):
        """Test st.text."""
        dg = st.text('some text')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, 'some text')
        self.assertEqual(el.text.format, protobuf.Text.PLAIN)

    def test_st_title(self):
        """Test st.title."""
        dg = st.title('some title')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, '# some title')
        self.assertEqual(el.text.format, protobuf.Text.MARKDOWN)

    def test_st_vega_lite_chart(self):
        """Test st.vega_lite_chart."""
        pass

    def test_st_video(self):
        """Test st.video."""
        # TODO(armando): generate real video data
        # For now it doesnt matter cause browser is the one that uses it.
        fake_video_data = '\x11\x22\x33\x44\x55\x66'.encode('utf-8')

        dg = st.video(fake_video_data)

        el = get_last_delta_element(dg)
        # Manually base64 encoded payload above via
        # base64.b64encode(bytes('\x11\x22\x33\x44\x55\x66'.encode('utf-8')))
        self.assertEqual(el.video.data, 'ESIzRFVm')
        self.assertEqual(el.video.format, 'video/mp4')

    def test_st_warning(self):
        """Test st.warning."""
        dg = st.warning('some warning')

        el = get_last_delta_element(dg)
        self.assertEqual(el.text.body, 'some warning')
        self.assertEqual(el.text.format, protobuf.Text.WARNING)

    def test_st_native_chart(self):
        """Test st._native_chart."""
        df = pd.DataFrame([[10, 20, 30]], columns=['a', 'b', 'c'])
        chart = Chart(df, 'line_chart', width=640, height=480)
        dg = st._native_chart(chart)

        el = get_last_delta_element(dg)
        self.assertEqual(el.chart.type, 'LineChart')
        self.assertEqual(el.chart.width, 640)
        self.assertEqual(el.chart.height, 480)
        self.assertEqual(
            el.chart.data.columns.plain_index.data.strings.data,
            ['a', 'b', 'c']
        )
        data = json.loads(json_format.MessageToJson(el.chart.data.data))
        result = [x['int64s']['data'][0] for x in data['cols']]
        self.assertEqual(result, ['10', '20', '30'])

    def test_st_text_exception(self):
        """Test st._text_exception."""
        data ={
            'type': 'ModuleNotFoundError',
            'message': 'No module named \'numpy\'',
            'stack_trace': [
                'Traceback (most recent call last):',
                '  File "<stdin>", line 1, in <module>',
                'ModuleNotFoundError: No module named \'numpy\'',
            ]
        }

        dg = st._text_exception(
            data.get('type'),
            data.get('message'),
            data.get('stack_trace'),
        )

        el = get_last_delta_element(dg)
        self.assertEqual(el.exception.type, data.get('type'))
        self.assertEqual(el.exception.message, data.get('message'))
        self.assertEqual(el.exception.stack_trace, data.get('stack_trace'))



class StreamlitWriteTest(unittest.TestCase):
    """Test st.write.

    Unit tests for https://streamlit.io/secret/docs/api/text.html#streamlit.write

    Because we're going to test st.markdown, st.pyplot, st.altair_chart
    later on, we don't have to test it in st.write In st.write, all we're
    trying to check is that the right st.* method gets called
    """

    def test_string(self):
        """Test st.write with a string."""
        with patch('streamlit.markdown') as p:
            st.write('some string')

            p.assert_called_once()

        with patch('streamlit.markdown') as p:
            st.write('more', 'strings', 'to', 'pass')

            p.assert_called_once_with('more strings to pass')

    def test_dataframe(self):
        """Test st.write with dataframe."""
        data = {
            'DataFrame': pd.DataFrame([[20, 30, 50]], columns=['a', 'b', 'c']),
            'Series': pd.Series(np.array(['a', 'b', 'c'])),
            'Index': pd.Index(list('abc')),
            'ndarray': np.array(['a', 'b', 'c']),
            'Styler': pd.DataFrame({'a': [1], 'b': [2]}).style.format('{:.2%}'),
        }

        # Make sure we have test cases for all _DATAFRAME_LIKE_TYPES
        self.assertEqual(sorted(data.keys()), sorted(st._DATAFRAME_LIKE_TYPES))

        for df in data.values():
            with patch('streamlit.dataframe') as p:
                st.write(df)

                p.assert_called_once()

    def test_exception_type(self):
        """Test st.write with exception."""
        with patch('streamlit.exception') as p:
            st.write(Exception('some exception'))

            p.assert_called_once()

    def test_help(self):
        """Test st.write with help types."""
        # Test module
        with patch('streamlit.help') as p:
            st.write(np)

            p.assert_called_once()

        # Test function
        with patch('streamlit.help') as p:
            st.write(st.set_option)

            p.assert_called_once()

    @patch('streamlit.util.is_type')
    def test_altair_chart(self, is_type):
        """Test st.write with altair_chart."""
        is_type.return_value = True

        class FakeChart(object):
            pass

        with patch('streamlit.altair_chart') as p:
            st.write(FakeChart())

            p.assert_called_once()

    @patch('streamlit.util.is_type')
    def test_pyplot(self, is_type):
        """Test st.write with matplotlib."""
        is_type.side_effect = [False, True]

        class FakePyplot(object):
            pass

        with patch('streamlit.pyplot') as p:
            st.write(FakePyplot())

            p.assert_called_once()

    def test_dict(self):
        """Test st.write with dict."""
        with patch('streamlit.json') as p:
            st.write({'a': 1, 'b': 2})

            p.assert_called_once()

    def test_default_object(self):
        """Test st.write with default clause ie some object."""
        class SomeObject(object):
            def __str__(self):
                return '1 * 2 - 3 = 4 !'

        with patch('streamlit.markdown') as p:
            st.write(SomeObject())

            p.assert_called_once_with(u'`1 \\* 2 \\- 3 \\= 4 \\!`')

    def test_exception(self):
        """Test st.write that raises an exception."""
        with patch('streamlit.markdown') as m, patch('streamlit.exception') as e:
            m.side_effect = Exception('some exception')
            st.write('some text')

            e.assert_called_once()

    def test_spinner(self):
        """Test st.spinner."""
        # TODO(armando): Test that the message is actually passed to
        # message.warning
        with patch('streamlit.empty') as e:
            with st.spinner('some message'):
                time.sleep(0.15)
            e.assert_called_once_with()
