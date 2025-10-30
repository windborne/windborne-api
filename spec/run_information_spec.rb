describe 'run_information' do
  it 'gets run information' do
    init_times = run('init_times', '--model', 'wm4')
    latest_line = init_times.split("\n").find { |l| l.start_with?('Latest initialization time:') }
    latest_time = latest_line.split(': ', 2)[1]

    output = run('run_information', '--model', 'wm4', latest_time)
    expect(output).to include('Initialization time:')
    expect(output).to include('Available forecast hours:')
    expect(output.split("\n").size).to be > 4

    first_line = output.split("\n").first
    expect(first_line).to match(/Initialization time: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
  end

  it 'gets run information with an ensemble member' do
    init_times = run('init_times', '--model', 'wm4-ens', '--ens-member', 'mean')
    latest_line = init_times.split("\n").find { |l| l.start_with?('Latest initialization time:') }
    latest_time = latest_line.split(': ', 2)[1]

    output = run('run_information', '--model', 'wm4-ens', '--ens-member', 'mean', latest_time)
    expect(output).to include('Available forecast hours:')
    expect(output.split("\n").size).to be > 1
  end
end


