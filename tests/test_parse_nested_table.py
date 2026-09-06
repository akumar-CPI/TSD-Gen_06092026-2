from scripts.generate_tsd import parse_nested_table

def test_parse_nested_table_basic():
    input_html = """
    <row>
      <cell id="Action">Set</cell>
      <cell id="Name">OrderId</cell>
      <cell id="Type">Header</cell>
      <cell id="Datatype">String</cell>
      <cell id="Value">12345</cell>
    </row>
    <row>
      <cell id="Action">Clear</cell>
      <cell id="Name">Temp</cell>
      <cell id="Type">Property</cell>
      <cell id="Datatype">String</cell>
      <cell id="Value"></cell>
    </row>
    """
    rows = parse_nested_table(input_html)
    assert isinstance(rows, list)
    assert len(rows) == 2
    assert rows[0]["Action"] == "Set"
    assert rows[0]["Name"] == "OrderId"
    assert rows[1]["Action"] == "Clear"
    assert rows[1]["Name"] == "Temp"
