wfsOutputExtension: QGIS Server Plugin to add Output Formats to WFS GetFeature request.
==========================================================================================

Description
---------------

wfsOutputExtension is a QGIS Server Plugin. It extends OGC Web Feature Service capabilities. It adds Output Formats to WFS GetFeature request.

It adds:
* KML
* ESRI ShapeFile as ZIP file
* MapInfo TAB as ZIP file
* MIF/MID File as ZIP file
* CSV, the datatable
* XLSX, the datatable
* ODS, the datatable

CSV, XLSX and ODS needs QGIS Server 2.8.4 or 2.12. If you build QGIS Server, you need the commit ae90d8ee6a6673f1c8b6d7cf3e8d69053e0d4a9b in 2.8 or f67234406c4e1fddb4ed440b936a925239d47f72 in 2.10.


Install on Ubuntu
------------------

Python plugins support for QGIS Server has been introduced with QGIS 2.8 and it is enabled by default on most distributions.

You'll find how to install QGIS Server in the QGIS documentation : http://docs.qgis.org/2.8/en/docs/user_manual/working_with_ogc/ogc_server_support.html

Prerequisites
_______________

We assume that you are working on a fresh install with Apache and FCGI module installed with:

```bash
$ sudo apt-get install apache2 libapache2-mod-fcgid
$ # Enable FCGI daemon apache module
$ sudo a2enmod fcgid
```

Package installation
_____________________

First step is to add debian gis repository, add the following repository:

```bash
$ cat /etc/apt/sources.list.d/debian-gis.list
deb http://qgis.org/debian trusty main
deb-src http://qgis.org/debian trusty main
 
$ # Add keys
$ sudo gpg --recv-key DD45F6C3
$ sudo gpg --export --armor DD45F6C3 | sudo apt-key add -
 
$ # Update package list
$ sudo apt-get update && sudo apt-get upgrade
```

Now install qgis server:

```bash
$ sudo apt-get install qgis-server python-qgis
```

Install wfsOutputExtension plugin
__________________________________

```bash
$ sudo mkdir -p /opt/qgis-server/plugins
$ cd /opt/qgis-server/plugins
$ sudo wget https://github.com/3liz/qgis-wfsOutputExtension/archive/master.zip
$ # In case unzip was not installed before:
$ sudo apt-get install unzip
$ sudo unzip master.zip 
$ sudo mv qgis-wfsOutputExtension-master wfsOutputExtension
```

Apache virtual host configuration
__________________________________

We are installing the server in a separate virtual host listening on port 81.

Let Apache listen to port 81:

```bash
$ cat /etc/apache2/conf-available/qgis-server-port.conf
Listen 81
$ sudo a2enconf qgis-server-port
```

The virtual host configuration, stored in /etc/apache2/sites-available/001-qgis-server.conf:

```
    <VirtualHost *:81>
        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html
     
        ErrorLog ${APACHE_LOG_DIR}/qgis-server-error.log
        CustomLog ${APACHE_LOG_DIR}/qgis-server-access.log combined
     
        # Longer timeout for WPS... default = 40
        FcgidIOTimeout 120 
        FcgidInitialEnv LC_ALL "en_US.UTF-8"
        FcgidInitialEnv PYTHONIOENCODING UTF-8
        FcgidInitialEnv LANG "en_US.UTF-8"
        FcgidInitialEnv QGIS_DEBUG 1
        FcgidInitialEnv QGIS_SERVER_LOG_FILE /tmp/qgis-000.log
        FcgidInitialEnv QGIS_SERVER_LOG_LEVEL 0
        FcgidInitialEnv QGIS_PLUGINPATH "/opt/qgis-server/plugins"
     
        # ABP: needed for QGIS HelloServer plugin HTTP BASIC auth
        <IfModule mod_fcgid.c>
            RewriteEngine on
            RewriteCond %{HTTP:Authorization} .
            RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
        </IfModule>
     
        ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
        <Directory "/usr/lib/cgi-bin">
            AllowOverride All
            Options +ExecCGI -MultiViews +FollowSymLinks
            Require all granted
            #Allow from all
      </Directory>
    </VirtualHost>
```

Enable the virtual host and restart Apache:

```bash
$ sudo a2ensite 001-qgis-server
$ sudo service apache2 restart
```

Test
_____

Open the link: **http://localhost/qgis_mapserv.fcgi?SERVICE=WFS&REQUEST=GetCapabilities&MAP=/path/to/a_qgis_project.qgs**

Replace **/path/to/a_qgis_project.qgs** to a real path
