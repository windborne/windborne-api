describe 'variables' do
  it 'gets a list of variables and levels' do
    output = run('variables', '--model', 'wm4')
    expect(output).to include('Surface variables:')
    expect(output).to include('Upper variables:')
    expect(output).to include('Levels:')
    expect(output.split("\n").size).to be > 4
  end
end


