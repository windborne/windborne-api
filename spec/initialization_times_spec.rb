describe 'init_times' do
  it 'gets a list of initialization times' do
    output = run('init_times')
    expect(output).to include('Latest initialization time:')
    expect(output).to include('Available initialization times:')
    expect(output.split("\n").size).to be > 4

    first_line = output.split("\n").first
    expect(first_line).to match(/Latest initialization time: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
  end

  it 'gets a list of initialization times with an ensemble member' do
    output = run('init_times', '--ens-member', '1')
    expect(output).to include('Available initialization times:')
    expect(output.split("\n").size).to be > 4
  end

  it 'gets a list of initialization times with intracycle' do
    output = run('init_times', '--intracycle')
    expect(output).to include('Available initialization times:')
    expect(output.split("\n").size).to be > 4
  end


end
