from distutils.core import setup

pkg = 'Extensions.NewsReader'
setup (name='enigma2-plugin-extensions-newsreader',
       version='0.1',
       description='RSS newsreader',
       package_dir={pkg: 'plugin'},
       packages=[pkg],
       data_files=[('/etc', 
           ['plugin/data/feeds.xml'])]
       )
