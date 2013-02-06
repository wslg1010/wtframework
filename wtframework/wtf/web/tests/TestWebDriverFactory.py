'''
Created on Dec 20, 2012

@author: "David Lai"
'''
from mox import Mox
from wtframework.wtf.config.ConfigReader import ConfigReader,\
    WTF_CONFIG_READER
from wtframework.wtf.web.WebDriverFactory import WebDriverFactory
import unittest
import yaml



class TestWebDriverFactory(unittest.TestCase):
    '''
    Test the WebDriverFactory creates webdriver based on config.
    
    Note: most of these tests will be commented out because they many call physical browsers 
    or call external services that may bill us.
    '''

    _mocker = None # Mox() mocking lib.
    _driver = None

    def setUp(self):
        #create an instance of Mox() to mock out config.
        self._mocker = Mox()

    def tearDown(self):
        self._mocker = None

        #tear down any webdrivers we create.
        try:
            self._driver.close()
        except:
            pass
        self._driver = None

    @unittest.skip("This test fails on CI")
    def test_createWebDriver_WithHtmlUnitDriver(self):
        "Simple unit test to check if instantiating an HTMLUnit driver works."
        config_reader = self._mocker.CreateMock(ConfigReader)
        config_reader.get_value(WebDriverFactory.SHUTDOWN_HOOK_CONFIG).InAnyOrder().AndReturn(True)
        config_reader.get_value(WebDriverFactory.DRIVER_TYPE_CONFIG).InAnyOrder().AndReturn("LOCAL")
        config_reader.get_value(WebDriverFactory.BROWSER_TYPE_CONFIG).InAnyOrder().AndReturn("HTMLUNIT")
        config_reader.get_value_or_default("selenium.server", \
                                                 WebDriverFactory._DEFAULT_SELENIUM_SERVER_FOLDER)\
                                                 .InAnyOrder()\
                                                 .AndReturn(WebDriverFactory._DEFAULT_SELENIUM_SERVER_FOLDER)
        self._mocker.ReplayAll()

        driver_factory = WebDriverFactory(config_reader)
        self._driver = driver_factory.create_webdriver()
        self._driver.get("http://www.google.com/")
        print "page title:", self._driver.title
        self._driver.find_element_by_name("q") #Google's famous 'q' element.


    @unittest.skip("Tests using real browser skipped by default")
    def test_createWebDriver_WithLocalBrowser(self):
        '''
        This will test this by opening firefox and trying to fetch Google with it.

        This test will normally be commented out since it spawns annoying browser windows.
        When making changes to WebDriverFactory, please run this test manually.
        '''
        config_reader = self._mocker.CreateMock(ConfigReader)
        config_reader.get_value(WebDriverFactory.SHUTDOWN_HOOK_CONFIG).InAnyOrder().AndReturn(True)
        config_reader.get_value(WebDriverFactory.DRIVER_TYPE_CONFIG).InAnyOrder().AndReturn("LOCAL")
        config_reader.get_value(WebDriverFactory.BROWSER_TYPE_CONFIG).InAnyOrder().AndReturn("FIREFOX")
        self._mocker.ReplayAll()
        
        driver_factory = WebDriverFactory(config_reader)
        driver = driver_factory.create_webdriver()
        driver.get("http://www.google.com")
        driver.find_element_by_name('q') #google's famous q element.


    @unittest.skip("Tests using external grid skipped by default.")
    def test_createWebDriver_WithGrid(self):
        '''
        This will test a grid setup by making a connection to Sauce Labs.

        This test will normally be commented out since it will use billable automation hours 
        on sauce labs.
        '''
        config_reader = MockConfigWithSauceLabs()
        
        driver_factory = WebDriverFactory(config_reader)
        self._driver = driver_factory.create_webdriver()
        exception = None
        try:
            self._driver.get('http://saucelabs.com/test/guinea-pig')
            self.assertGreater(self._driver.session_id, 0, "Did not get a return session id from Sauce.")
        except Exception as e:
            exception = e
        finally:
            # Make sure we quit sauce labs webdriver to avoid getting billed additonal hours.
            try:
                self._driver.quit()
            except:
                pass
        
        if exception != None:
            raise e

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()



class MockConfigWithSauceLabs(object):
    '''
    Mock config that returns sauce labs connection string.
    '''
    map = None
    
    def __init__(self):
        config = """
        selenium:
            type: REMOTE
            remote_url: {0}
            browser: FIREFOX
            desired_capabilities:
                version: 16.0
                platform: Windows 2008
                name: Unit Testing WD-acceptance-tests WebDriverFactory
        """.format(WTF_CONFIG_READER.get_value("selenium.remote_url"))
        # TODO: Might be good to replace this with a local grid to avoid using up SauceLab automation hours.
        self.map = yaml.load(config)



    def get_value(self,key):
        '''
        Gets the value from the yaml config based on the key.
        
        No type casting is performed, any type casting should be 
        performed by the caller.
        '''
        if "." in key:
            #this is a multi levl string
            namespaces = key.split(".")
            temp_var = self.map
            for name in namespaces:
                temp_var = temp_var[name]
            return temp_var
        else:
            value = self.map[key]
            return value                
