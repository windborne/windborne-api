describe 'calculation_times degree_days' do
  it 'prints available calculation times to stdout' do
    output = run('calculation_times', 'degree_days', '--model', 'wm4')
    expect(output).to include('Latest calculation time:')
    expect(output).to include('Available calculation times:')
    expect(output.split("\n").size).to be > 4

    first_line = output.split("\n").first
    expect(first_line).to match(/Latest calculation time: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
    expect(output.downcase).not_to include('traceback')
  end

  it 'works with an ensemble member' do
    output = run('calculation_times', 'degree_days', '--model', 'wm-4.5-ens', '--ens-member', 'mean')
    expect(output).to include('Available calculation times:')
    expect(output.split("\n").size).to be > 1
  end
end
