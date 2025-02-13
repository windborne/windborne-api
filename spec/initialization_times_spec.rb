describe 'init_times' do
  it 'gets a list of initialization times' do
    output = run('init_times')
    expect(output).to include('Latest initialization time:')
    expect(output).to include('Available initialization times:')
    expect(output.split("\n").size).to be > 4

    first_line = output.split("\n").first
    expect(first_line).to match(/Latest initialization time: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
  end
end