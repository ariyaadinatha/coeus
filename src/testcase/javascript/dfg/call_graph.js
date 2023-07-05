function test(req){
  source = req.body.get('domain');
  sink(source);
}

function sink(command){
  eval(command);
}