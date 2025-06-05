describe 'generation_times' do
  it 'gets a list of generation times' do
    output = run('generation_times')
    expect(output).to include('Generation times:')
    # Match initialization time line: " - 2025-06-03T00:00:00+00:00:"
    expect(output).to match(/^ - \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}:$/m)
    # Match forecast hour line: "   - 0: 2025-06-03T08:17:16.505002+00:00"
    expect(output).to match(/^   - \d+: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2}$/m)
  end

  it 'gets a list of generation times with an ensemble member' do
    output = run('generation_times', '--ens-member', '1')
    expect(output).to include('Generation times:')
    # Match initialization time line: " - 2025-06-03T00:00:00+00:00:"
    expect(output).to match(/^ - \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}:$/m)
    # Match forecast hour line: "   - 0: 2025-06-03T08:17:16.505002+00:00"
    expect(output).to match(/^   - \d+: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2}$/m)
  end

  it 'gets a list of generation times with intracycle' do
    output = run('generation_times', '--intracycle')
    expect(output).to include('Generation times:')
    # Match initialization time line: " - 2025-06-03T00:00:00+00:00:"
    expect(output).to match(/^ - \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}:$/m)
    # Match forecast hour line: "   - 0: 2025-06-03T08:17:16.505002+00:00"
    expect(output).to match(/^   - \d+: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2}$/m)
  end
end
