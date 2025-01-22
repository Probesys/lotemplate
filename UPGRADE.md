Upgrades
========

From 1.x to 2.x
---------------

### API : secretkey field

In all the API requests, the field secret_key is now named secretkey (due to upgrade of Flask).

before :

```bash
curl -X GET -H 'secret_key: my_secret_key' http://lotemplate:8000/
```

after :

```bash
curl -X GET -H 'secretkey: my_secret_key' http://lotemplate:8000/
```

### API : JSON to send in order to generate file is not an array anymore

Look at the following example : The JSON sent was an array in the previous version. Now it is directly the dict that was inside the array.

before :

```bash
 curl -X POST -H 'secret_key: my_secret_key' -H 'Content-Type: application/json' -d '[{"name":"my_file.odt","variables":{"my_tag":{"type":"text","value":"foo"},"other_tag":{"type":"text","value":"bar"}}}]' --output titi.odt http://lotemplate:8000/test_dir1/basic_test.odt 
```

after :

```bash
 curl -X POST -H 'secretkey: my_secret_key' -H 'Content-Type: application/json' -d '{"name":"my_file.odt","variables":{"my_tag":{"type":"text","value":"foo"},"other_tag":{"type":"text","value":"bar"}}}' --output titi.odt http://lotemplate:8000/test_dir1/basic_test.odt 
```