require 'open3'
require 'json'

def run(*args, wb_client_id: 'global', wb_api_key: nil, print: nil)
  print = true if print.nil? && (ARGV.include?('--print') || ENV['PRINT']&.start_with?('t'))

  if wb_client_id == 'global' || wb_client_id == 'user'
    credentials = JSON.parse(File.read(__dir__ + '/credentials.json'))
    wb_api_key = credentials["#{wb_client_id}_api_key"]
    wb_client_id = credentials["#{wb_client_id}_client_id"]
  end

  # WARNING: DO NOT COMMIT THESE CHANGES -- it's just cursor fuckery
  env = {
    'WB_CLIENT_ID' => wb_client_id,
    'WB_API_KEY' => wb_api_key,
    'PYTHONUNBUFFERED' => '1',
    'PYTHONPATH' => File.expand_path('..', __dir__)
  }

  # Run the CLI via Python module so we don't require console-script install
  command = ['python3', '-m', 'windborne.cli', *args]

  output = ''
  status = nil

  # Use Open3.popen2e to combine stdout and stderr
  Open3.popen2e(env, *command) do |stdin, stdout_and_stderr, wait_thread|
    stdin.close  # We don't need stdin for this case

    # Read output stream and process it line by line
    stdout_and_stderr.each_line do |line|
      puts line if print
      output += line
    end

    # Get the process status
    status = wait_thread.value
  end

  # Raise an error if the command failed
  unless status.success?
    puts "Command '#{command}' failed with exit status #{status.exitstatus}" if print
  end

  # Return the accumulated output
  output
end


if __FILE__ == $PROGRAM_NAME
  run(*ARGV, print: true)
end