require 'tmpdir'

describe 'tropical_cyclones' do
  def expect_cyclone_output(*args, details: false)
    Dir.mktmpdir('windborne-cyclones') do |directory|
      output_path = File.join(directory, 'cyclones.json')
      run('tropical_cyclones', *args, output_path)

      # Pin the print request to the saved response's run, so a newly published
      # forecast cannot change the expected storm set between the two requests.
      expect(File.exist?(output_path)).to be true
      response = JSON.parse(File.read(output_path))
      expect(response).to include('initialization_time', 'tropical_cyclones')
      expect(response['tropical_cyclones']).to be_a(Hash)
      expect(response['initialization_time']).to be_a(String)
      output = run('tropical_cyclones', *args, '--initialization-time', response['initialization_time'])
      expect(output).to include("Tropical Cyclones for initialization time: #{response['initialization_time']}")

      cyclones = response['tropical_cyclones']
      if cyclones.empty?
        expect(output).to include('No tropical cyclones for this request.')
        expect(output).not_to include('Cyclone ID:')
      else
        expect(output).not_to include('No tropical cyclones for this request.')
        cyclones.each do |cyclone_id, cyclone|
          expect(output).to include("Cyclone ID: #{cyclone_id}\n")
          storm_output = output.split("Cyclone ID: #{cyclone_id}\n", 2).last.split("\nCyclone ID:", 2).first
          expect(storm_output).to include('Storm', 'Start', 'End', 'Max wind (kt)', 'Min pressure (hPa)')

          if details
            path = cyclone.fetch('path') { cyclone.fetch('mean_path') }
            expect(path).to be_an(Array)
            if path.any?
              expect(storm_output).to include('Time', 'Latitude', 'Longitude')
            else
              expect(storm_output).not_to include('Latitude', 'Longitude')
            end
          else
            expect(storm_output).not_to include('Latitude', 'Longitude')
          end
        end
      end
    end
  end

  it 'prints wm-6 summaries by default, or the current no-cyclones message' do
    expect_cyclone_output
  end

  it 'prints wm-6 summaries and available tracks when details are requested' do
    expect_cyclone_output('--model', 'wm-6', '--include-details', 'true', details: true)
  end
end

