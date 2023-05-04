from distutils.core import setup
import setup_translate

pkg = 'Extensions.NewsReader'
setup(name='enigma2-plugin-extensions-newsreader',
       version='1.0',
       description='NewsReader for reading RSS-feeds',
       packages=[pkg],
       package_dir={pkg: 'plugin'},
       package_data={pkg: ['*.png', 'locale/*/LC_MESSAGES/*.mo']},
       data_files=[('/etc', ['plugin/data/feeds.xml'])],
       cmdclass=setup_translate.cmdclass,  # for translation
      )
