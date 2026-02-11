sub get_params {

  ## First, grab any GET stuff (overrides POST)
  if ($ENV{'REQUEST_METHOD'} eq "GET") {
    $querystring = $ENV{'QUERY_STRING'}
  }
  ## Could change this to a simple "if" to allow GET *and* POST
  elsif ($ENV{'REQUEST_METHOD'} eq 'POST' && 
         $ENV{'CONTENT_TYPE'} eq "application/x-www-form-urlencoded") {
    ## Okay if CONTENT_LENGTH is 0...
    read(STDIN, $querystring, $ENV{CONTENT_LENGTH});

    $ENV{"REQUEST_METHOD"} = "GET";
    $ENV{"QUERY_STRING"} = $querystring;
  }
  else { ## Last ditch efforts, no REQUEST METHOD found
    ## Any GET info?
    $querystring = $ENV{'QUERY_STRING'};
    ## Any POST info?
    $querystring || read(STDIN, $querystring, $ENV{CONTENT_LENGTH});

    $ENV{"REQUEST_METHOD"} = "GET";
    $ENV{"QUERY_STRING"} = $querystring;
  }

  ## Find all of our params:
  for (split(/\&/, $querystring)) {
    if (($param_name, $param_value) = /(.*)=(.*)/) { ## Normal...
      $param_value =~ tr/+/ /;
      $param_value =~ s/%(..)/pack('c',hex($1))/eg;
    }
    else { ## Abnormal...
      $param_name = $_; $param_value = "0";
    }
    $param_name =~ tr/+/ /;
    $param_name =~ s/%(..)/pack('c',hex($1))/eg;
    $params++;

    if (defined $param{$param_name}) { ## Allows for "0" cases....
      $param{$param_name} .= '#' . $param_value;
    }
    else {
      $param{$param_name} = $param_value;
    }

    $ENV{$param_name} = $param_value;
  }
}

sub print_env () {
  my ($keyword, $value);
  while (($keyword, $value) = each(%ENV)) {
    print "$keyword = $value\n";
  }
}

1;
