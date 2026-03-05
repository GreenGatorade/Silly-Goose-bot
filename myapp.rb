require 'sinatra'
require 'json'

get '/' do
  @messages = JSON.parse(File.read('messages.json')) rescue []
  erb :index
end
