describe 'tropical_cyclones' do
  it 'prints current tropical cyclones or a no-cyclones message with details' do
    output = run('tropical_cyclones')
    return if output.include?('There are no active tropical cyclones for your request')
      
    expect(output).to include('Tropical Cyclones for initialization time:')
    expect(output).to include('Cyclone ID:')
    # Table headers from print_table
    expect(output).to include('Time')
    expect(output).to include('Latitude')
    expect(output).to include('Longitude')
  end

  it 'accepts a model parameter and behaves similarly' do
    output = run('tropical_cyclones', '--model', 'wm4')
    return if output.include?('There are no active tropical cyclones for your request')

    expect(output).to include('Tropical Cyclones for initialization time:')
    expect(output).to include('Cyclone ID:')
    expect(output).to include('Time')
    expect(output).to include('Latitude')
    expect(output).to include('Longitude')
  end
end

